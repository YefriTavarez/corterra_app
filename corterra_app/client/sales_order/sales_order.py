# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

from typing import TYPE_CHECKING

import frappe

if TYPE_CHECKING:
	from erpnext.selling.doctype.sales_order import sales_order

__all__ = (
	"make_production_order",
)


@frappe.whitelist()
def make_production_order(sales_order_id: str):
	doctype = "Orden de Produccion"

	order = get_sales_order(sales_order_id)

	# order.



def get_sales_order(name: str) -> "sales_order.SalesOrder":
	doctype = "Sales Order"
	return frappe.get_doc(doctype, name)
