# Copyright (c) 2026, Yefri Tavarez and Contributors
# For license information, please see license.txt

from __future__ import annotations

from typing import Any

import frappe

from nubef.api.alanube_company import get_alanube_company_details, is_alanube_company
from nubef.api.invoice_submission import SENDABLE_NCF_STATUSES
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


def get_alanube_fiscal_companies() -> list[str]:
	"""Return ERPNext company names configured for nubef-managed eNCF."""
	return frappe.get_all(
		"Alanube Company",
		filters={"enabled": 1, "manage_ncfs_from_alanubes": 1},
		pluck="company",
	) or []


def get_pending_sales_invoice_names() -> list[str]:
	"""Return submitted Sales Invoices that still need eNCF assignment or Alanube send."""
	companies = get_alanube_fiscal_companies()
	if not companies:
		return []

	sendable_statuses = [status for status in SENDABLE_NCF_STATUSES if status]

	missing_ncf = frappe.get_all(
		"Sales Invoice",
		filters={
			"docstatus": 1,
			"company": ["in", companies],
		},
		or_filters=[
			["ncf", "is", "not set"],
			["ncf", "=", ""],
		],
		pluck="name",
	)

	pending_send = frappe.get_all(
		"Sales Invoice",
		filters={
			"docstatus": 1,
			"company": ["in", companies],
			"ncf_status": ["in", sendable_statuses],
		},
		or_filters=[
			["ncf", "is", "set"],
			["ncf", "!=", ""],
		],
		pluck="name",
	)

	return list(dict.fromkeys(missing_ncf + pending_send))


def process_pending_sales_invoice_fiscal() -> None:
	"""Hourly scheduler entry: assign eNCF and send pending submitted invoices to Alanube."""
	for sales_invoice_name in get_pending_sales_invoice_names():
		try:
			process_sales_invoice_fiscal(sales_invoice_name)
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			frappe.log_error(
				title=f"Sales Invoice fiscal processing failed for {sales_invoice_name}",
				message=frappe.get_traceback(),
			)


def process_sales_invoice_fiscal(sales_invoice_name: str) -> bool:
	"""Assign eNCF (if missing) and send a submitted invoice to Alanube when applicable."""
	doc = frappe.get_doc("Sales Invoice", sales_invoice_name)
	if doc.docstatus != 1 or not should_use_nubef_fiscal(doc):
		return False

	processed = False
	if not doc.ncf:
		if assign_encf_to_invoice(doc):
			doc.reload()
			processed = True

	if doc.ncf and send_pending_invoice_to_alanube(doc):
		processed = True

	return processed


def assign_encf_to_invoice(doc: Any) -> bool:
	"""Assign the next eNCF from nubef NCF Sequence when the invoice has none."""
	if getattr(doc, "docstatus", 0) not in (0, 1):
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

	if doc.docstatus == 1:
		_persist_submitted_encf(doc, ncf, sequence_due_date)

	return True


def send_pending_invoice_to_alanube(doc: Any) -> bool:
	"""Send a submitted invoice to Alanube when it has a sendable NCF status."""
	if getattr(doc, "docstatus", 0) != 1:
		return False
	if not getattr(doc, "ncf", None):
		return False
	if getattr(doc, "ncf_status", None) not in SENDABLE_NCF_STATUSES:
		return False

	_send_to_alanube(doc.name)
	return True


def _persist_submitted_encf(doc: Any, ncf: str, sequence_due_date) -> None:
	needs_full_save = bool(doc.get("return_against") and doc.get("dgii_additional_information"))
	if needs_full_save:
		doc.flags.ignore_permissions = True
		doc.save()
		return

	doc.db_set(
		{
			"ncf": ncf,
			"sequence_due_date": sequence_due_date,
		}
	)


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
