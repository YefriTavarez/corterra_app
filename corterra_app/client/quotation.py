# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe
from frappe import _

from frappe.utils import getdate, nowdate


from erpnext.selling.doctype.quotation.quotation import _make_sales_order


@frappe.whitelist()
def make_sales_order(source_name: str, target_doc=None):
    if not frappe.db.get_singles_value(
        "Selling Settings", "allow_sales_order_creation_for_expired_quotation"
    ):
        quotation = frappe.db.get_value(
            "Quotation", source_name, ["transaction_date", "valid_till"], as_dict=1
        )
        if quotation.valid_till and (
            quotation.valid_till < quotation.transaction_date or quotation.valid_till < getdate(nowdate())
        ):
            frappe.throw(_("Validity period of this quotation has ended."))

    return _make_sales_order(source_name, target_doc, ignore_permissions=True)
