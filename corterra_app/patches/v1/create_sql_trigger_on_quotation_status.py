# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt


import frappe


def execute():
	frappe.db.sql_ddl("""
		CREATE TRIGGER update_quotation_status
		BEFORE UPDATE ON `tabQuotation`
		FOR EACH ROW
		BEGIN
			IF NEW.status = 'Lost' THEN
				SET NEW.custom_estado_de_aprobacion = 'Vencido';
			END IF;
		END
	""")
