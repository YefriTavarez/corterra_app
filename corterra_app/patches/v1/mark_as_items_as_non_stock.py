# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe


def execute():
	for name in frappe.get_all("Item", filters={
		"is_stock_item": 1,
		"disabled": 0,
	}, pluck="name"):
		item = frappe.get_doc("Item", name)
		item.is_stock_item = 0
		item.db_update()
