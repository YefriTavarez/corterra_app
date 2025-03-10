# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe


def autoname(doc, method=None):
	if not doc.flags.production_order_id:
		frappe.throw("No se ha asociado una Orden de Producción a esta Nota de Entrega")
	
	production_order_id = doc.flags.production_order_id
	doc.name = production_order_id.replace("OPR-", "COND-")
