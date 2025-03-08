# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe

from erpnext.selling.doctype.sales_order import sales_order


# Workflow:
# ---------
# Once the Quotation is approved (by Customer and Manager) a Sales Order
# is created. This Sales Order will be used to create a Production Order.
# After completion of the Production Order, a Sales Invoice will be created.
# Finally, a Delivery Note will be created. They can be created in either way.


@frappe.whitelist()
def make_sales_invoice(production_order_id: str):
	# to create the Sales Invoice, we need to get the related Sales Order
	# and then use the ERPNext method they use to create the Sales Invoice
	prod = get_production_order(production_order_id)

	if not prod.sales_order:
		frappe.throw("No se ha asociado una Orden de Venta a esta Orden de Producción")

	sinv = sales_order.make_sales_invoice(
		source_name=prod.sales_order,
		target_doc=None,
		ignore_permissions=True,
	)

	if sinv.is_new():
		sinv.insert()

	try:
		sinv.submit()
	except Exception as e:
		frappe.log_error()
		return {
			"ok": False,
			"error": str(e),
		}

	return {
		"ok": True,
		"id": sinv.name,
	}


@frappe.whitelist()
def make_delivery_note(production_order_id: str):
	...


def get_production_order(name: str):
	doctype = "Orden de Produccion"
	return frappe.get_doc(doctype, name)
