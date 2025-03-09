# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe
from frappe.model import document


def on_submit(doc, method=None):
	generate_ncf(doc)


@frappe.whitelist()
def generate_ncf(doc, autosave=False):
	# if the doc is a string, we need to parse it
	if isinstance(doc, str):
		doc = frappe.parse_json(doc)

	if not isinstance(doc, document.Document):
		doc = frappe.get_doc(doc.doctype, doc.name)

	# if it's being cancelled and then resubmitted
	# we don't want to generate a new NCF
	if doc.amended_from:
		return "amended_invoice"
	
	# if it's a return, we need to remember the original NCF
	# and generate a new one
	if doc.is_return:
		# validate if the original invoice has an NCF
		# if not, we can't generate a return NCF
		if not doc.ncf:
			frappe.msgprint(
				"No se ha generado un NCF para esta factura"
			)
			return "return_no_ncf"

		# load the NCF for credit notes
		ncf = get_ncf_for_credit_note()

		# validate if we have a NCF for credit notes
		# if not, we can't generate a return NCF
		if not ncf:
			frappe.throw(
				"No se ha encontrado ningun Tipo de Comprobante para Notas de Credito"
			)

		# if the original invoice has an NCF, we need to remember it
		# and generate a new one
		doc.against_ncf = doc.ncf
	else:
		ncf = get_ncf(doc.customer)

		# validate if we have a NCF for this customer
		#
		# if not, we can't generate an NCF
		if not ncf:
			frappe.throw(
				"No se ha encontrado ningun Tipo de Comprobante para este cliente"
			)

	doc.ncf = _generate_ncf(ncf)
	doc.sequence_expiration = ncf.expiration_date

	# if we're autosaving, we have to save the document
	# before returning the NCF
	if autosave:
		if doc.docstatus == 2:
			frappe.throw(
				"No se puede guardar un documento cancelado"
			)
		elif doc.docstatus == 1:
			doc.db_update()
		else:
			doc.save()

	return doc.ncf

	
def _generate_ncf(ncf):
	if not ncf.current_value:
		ncf.current_value = 0

	ncf.current_value += 1

	if ncf.current_value > ncf.max_value:
		frappe.throw(
			f"Se ha alcanzado el limite de NCF para el Tipo de Comprobante {ncf.name!r}"
		)

	ncf.flags.ignore_mandatory = True
	ncf.flags.ignore_permissions = True
	ncf.save()

	return get_formatted(ncf.serie, ncf.current_value)


def get_ncf_for_credit_note():
	doctype = "Tipo de Comprobante"
	
	if name := frappe.db.exists(doctype, {
		"get_ncf_for_credit_note": 1,
	}):
		return frappe.get_doc(doctype, name)
	else:
		frappe.throw("No se ha encontrado un Tipo de Comprobante para Notas de Credito")


def get_ncf(customer):
	tax_category = get_customer_tax_category(customer)

	if not tax_category:
		frappe.throw(
			f"No se ha especificado una Categoria de Impuesto para el cliente {customer!r}"
		)
	
	doctype = "Tipo de Comprobante"
	if name := frappe.db.exists(doctype, {
		"tax_category": tax_category,
	}):
		return frappe.get_doc(doctype, name)


def get_customer_tax_category(name):
	doctype = "Customer"
	fieldname = "tax_category"

	return frappe.get_value(doctype, name, fieldname)


def get_formatted(serie, value):
	return f"{serie}{value:08d}"
