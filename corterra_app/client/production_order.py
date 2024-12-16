# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe


def autoname(doc, method=None):
	if not doc.flags.sales_order_id:
		frappe.throw("No se ha asociado una Orden de Venta a esta Orden de Producción")
	
	sales_order_id = doc.flags.sales_order_id
	doc.name = sales_order_id.replace("OVE-", "OPR-")
