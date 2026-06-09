# Copyright (c) 2026, Yefri Tavarez and Contributors
# For license information, please see license.txt

from __future__ import annotations

from typing import Any

import frappe

from nubef.api.alanube_company import get_alanube_company_details, is_alanube_company
from nubef.api.invoice_submission import (
	SENDABLE_NCF_STATUSES,
	apply_skip_auto_post_flag,
	should_defer_erpnext_submit_until_alanube_receipt,
)
from nubef.api.ncf_sequence import (
	get_sequence_info,
	get_sequence_name_for_credit_note,
	get_sequence_name_for_debit_note,
	get_suggested_sequence,
)


def should_use_nubef_fiscal(doc: Any) -> bool:
	"""Return whether this invoice should use nubef eNCF assignment and Alanube send."""
	company = getattr(doc, "company", None)
	if not company or not is_alanube_company(company):
		return False

	settings = get_alanube_company_details(company, raise_on_missing=False) or {}
	return bool(settings.get("enabled")) and bool(settings.get("manage_ncfs_from_alanubes"))


def assign_encf_to_invoice(doc: Any) -> bool:
	"""Assign the next eNCF from nubef NCF Sequence when the invoice has none."""
	if getattr(doc, "docstatus", 0) != 0:
		return False
	if not should_use_nubef_fiscal(doc):
		return False
	if getattr(doc, "ncf", None):
		return False

	sequence_name = _resolve_sequence_name(doc)
	if not sequence_name:
		frappe.throw(
			"No se encontró una secuencia N.C.F. sugerida para esta factura. "
			"Verifique las secuencias N.C.F. y la categoría de impuesto del cliente."
		)

	_sequence_id, ncf, sequence_due_date = get_sequence_info(sequence_name)
	doc.ncf = ncf
	doc.sequence_due_date = sequence_due_date
	_populate_dgii_reference_information(doc)
	doc.flags.corterra_encf_auto_assigned = True
	return True


def send_to_alanube_if_needed(doc: Any) -> bool:
	"""Send the invoice to Alanube when it was auto-assigned an eNCF in this submit flow."""
	if not _has_flag(doc, "corterra_encf_auto_assigned"):
		return False
	if _has_flag(doc, "corterra_encf_sent_to_alanube"):
		return False
	if not getattr(doc, "ncf", None):
		return False

	ncf_status = getattr(doc, "ncf_status", None)
	if ncf_status not in SENDABLE_NCF_STATUSES:
		return False

	_send_to_alanube(doc.name)
	apply_skip_auto_post_flag(doc, True)
	doc.flags.corterra_encf_sent_to_alanube = True
	return True


def ensure_encf_before_submit(doc: Any, method: str | None = None) -> None:
	"""Assign eNCF before submit and pre-send when Alanube receipt is required first."""
	if getattr(doc, "docstatus", 0) != 0:
		return

	assign_encf_to_invoice(doc)

	if should_defer_erpnext_submit_until_alanube_receipt(getattr(doc, "company", None)):
		send_to_alanube_if_needed(doc)


def send_encf_to_alanube(doc: Any, method: str | None = None) -> None:
	"""Send auto-assigned eNCF invoices to Alanube after ERPNext submit."""
	send_to_alanube_if_needed(doc)


def _resolve_sequence_name(doc: Any) -> str | None:
	if doc.get("is_return"):
		return get_sequence_name_for_credit_note(doc.company)
	if doc.get("is_debit_note"):
		return get_sequence_name_for_debit_note(doc.company)

	return get_suggested_sequence(
		company=doc.company,
		customer=doc.customer,
		tax_category=doc.get("tax_category") or "",
		is_return=bool(doc.get("is_return")),
		is_debit_note=bool(doc.get("is_debit_note")),
	)


def _populate_dgii_reference_information(doc: Any) -> None:
	if not doc.get("return_against"):
		return
	if doc.get("dgii_additional_information"):
		return

	if not frappe.db.exists("Sales Invoice", doc.return_against):
		frappe.throw(
			f"La factura referenciada en Contra Devolución ({doc.return_against}) no existe."
		)

	ref = frappe.get_doc("Sales Invoice", doc.return_against)
	tax_id = frappe.db.get_value("Customer", doc.customer, "tax_id") or ""

	ref_info = {
		"ncf_modified": ref.ncf,
		"ncf_modified_date": ref.posting_date,
		"rnc_other_taxpayer": tax_id,
	}

	if doc.get("is_debit_note"):
		ref_info["modification_code"] = "3- Corrige montos del NCF modificado"
		ref_info["reason_for_modification"] = "Corrige montos del NCF modificado"
	elif doc.get("is_return"):
		ref_info["modification_code"] = "1- Anulación total"
		ref_info["reason_for_modification"] = "Anulación total"

	doc.append("dgii_additional_information", ref_info)


def _send_to_alanube(document_id: str):
	from nubef.api.sales_invoice import send_to_alanube

	return send_to_alanube(document_id)


def _has_flag(doc: Any, key: str) -> bool:
	flags = getattr(doc, "flags", None)
	return bool(getattr(flags, key, False))
