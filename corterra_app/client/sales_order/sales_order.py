# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

from typing import TYPE_CHECKING

import frappe

if TYPE_CHECKING:
	from erpnext.selling.doctype.sales_order import sales_order

from . import helper


__all__ = (
	"make_production_order",
)


def autoname(doc, method):
	if not doc.custom_solicitar_cotizacion:
		frappe.throw("No se ha asociado una Solicitud de Cotización a esta Orden de Venta")

	doc.name = doc.custom_solicitar_cotizacion \
		.replace("SOL-", "OVE-")

def on_submit(doc, method):
	if doc.docstatus == 1:
		make_production_order(doc.name)


@frappe.whitelist()
def make_production_order(sales_order_id: str):
	# Orden de Produccion Fields
	# 'naming_series',
	# 'cliente',
	# 'fecha',
	# 'fecha_compromiso',
	# 'producto',
	# 'nombre_referencia',
	# 'calibre_material',
	# 'tipo_troquelado',
	# 'troqueladora',
	# 'posicion',
	# 'ancho_tablero',
	# 'alto_tablero',
	# 'margen_pinzas_in',
	# 'plecas_corte',
	# 'plecas_hendido',
	# 'plecas_perfora',
	# 'corte_hendido',
	# 'qr_url',
	doctype = "Orden de Produccion"

	order = get_sales_order(sales_order_id)

	if not order.custom_solicitar_cotizacion:
		frappe.throw("No se ha asociado una Solicitud de Cotización a esta Orden de Venta")

	details = get_details(order.custom_solicitar_cotizacion)

	# let's create the production order

	po = frappe.new_doc(doctype)
	po.update(details)

	po.update({
		"cliente": order.customer,
		"fecha": order.transaction_date,
		"fecha_compromiso": get_delivery_date(order),
	})

	po.flags.ignore_permissions = True

	po.flags.sales_order_id = sales_order_id

	try:
		po.save()
	except frappe.ValidationError as e:
		# we need to make sure the PO is created no matter what
		frappe.db.rollback()
		
		frappe.log_error()
		frappe.db.commit()

		po.flags.ignore_links = True
		po.flags.ignore_mandatory = True
		po.flags.ignore_validate = True

		po.insert()


def get_sales_order(name: str) -> "sales_order.SalesOrder":
	doctype = "Sales Order"
	return frappe.get_doc(doctype, name)


def get_delivery_date(order: "sales_order.SalesOrder") -> str:
	settings = get_settings()

	today = frappe.utils.nowdate()

	expected_delivery_days = frappe.utils.add_days(
		today, settings.lead_time_in_days
	)

	return helper.get_next_working_day(expected_delivery_days)


def get_settings():
	doctype = "Configuracion Corterra"
	return frappe.get_single(doctype)


def get_details(quotation_request_id) -> str:
	results = frappe.db.sql(f"""
		Select
			request.producto_cotizar As producto,
			request.referencia As nombre_referencia,
			request.calibre_material As calibre_material,
			request.tipo_troquelado As tipo_troquelado,
			request.troqueladora As troqueladora,
			request.alineado As posicion,
			request.ancho_tablero As ancho_tablero,
			request.alto_tablero As alto_tablero,
			request.pinzas As margen_pinzas_in,
			request.diseno As diseno,
			request.pdf_generado As pdf_generado,
			estimation.plecas_corte As plecas_corte,
			estimation.plecas_hendido As plecas_hendido,
			estimation.plecas_perfora As plecas_perfora,
			estimation.plecas_corte_hendido As corte_hendido
		From
			`tabSolicitar Cotizacion` As request
		Inner Join
			`tabEstimacion Costo` As estimation
			On estimation.solicitud_id = request.name
			And estimation.docstatus = 1
		Where
			request.name = {quotation_request_id!r}
	""", as_dict=True)

	if results:
		return results[0]
	
	raise frappe.ValidationError("No se encontró la Solicitud de Cotización asociada a la Orden de Venta {sales_order_id!r}")
