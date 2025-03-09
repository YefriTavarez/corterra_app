# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe


def execute():
    production_orders = frappe.get_all(
        "Orden de Produccion",
        filters={
            "name": ["like", "OPR-%"],
            "sales_order": "",
        },
        pluck="name"
    )

    for production_order_id in production_orders:
        production_order = frappe.get_doc("Orden de Produccion", production_order_id)
        
        sales_order_id = production_order_id.replace("OPR-", "OVE-")

        # check if the sales order exists
        # and has docstatus = 1
        if ovid := frappe.db.exists("Sales Order", sales_order_id):
            production_order.ov_number = ovid
            production_order.db_update()
            frappe.db.commit()
