# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe


def on_submit(doc, method=None):
	generate_ncf(doc)


@frappe.whitelist()
def generate_ncf(doc):
	# if it's being cancelled and then resubmitted
	# we don't want to generate a new NCF
	if doc.amended_from:
		return
	
	# if it's a return, we need to remember the original NCF
	# and generate a new one
	if doc.is_return:
		if not doc.ncf:
			frappe.msgprint(
				"No se ha generado un NCF para esta factura"
			)
			return

		doc.against_ncf = doc.ncf
		doc.ncf = _generate_ncf(doc, is_return=True)
	else:
		doc.ncf = _generate_ncf(doc)
	

def _generate_ncf(doc, is_return=False):
	if is_return:
		ncf = get_ncf_for_credit_note()
	else:
		ncf = get_ncf(doc.customer)

	if not ncf:
		frappe.throw(
			"No se ha encontrado ningun Tipo de Comprobante para este cliente"
		)
	
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
	return f"{serie}-{value:08d}"
