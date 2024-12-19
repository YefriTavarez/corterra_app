# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt


import frappe


def autoname(doc, method=None):
	doc.name = doc.custom_solicitar_cotizacion.replace("SOL-", "COT-")
