# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

import time
import shutil
from typing import TYPE_CHECKING

import frappe


if TYPE_CHECKING:
	from frappe.core.doctype.file import file


def on_update(doc: "file.File", *args: list):
	if doc.attached_to_doctype != "Solicitar Cotizacion":
		return # this cutomization applies only to Solicitar Cotizacion
	
	if doc.file_name.startswith("TO-") \
		or doc.file_name.startswith("TG-"):
		return # the current file is already named correctly

	if not doc.file_type == "PDF":
		frappe.throw("El archivo debe ser de tipo PDF")

	# remember the original file name
	original_filename = doc.file_name
	original_file_url = doc.file_url

	# rename the file
	if doc.attached_to_field == "pdf_generado":
		file_name = doc.attached_to_name \
			.replace("SOL-", "TG-")
	else:
		file_name = doc.attached_to_name \
			.replace("SOL-", "TO-")

	doc.file_name = f"{file_name}.pdf"

	file_url = doc.file_url.replace(original_filename, doc.file_name)

	# move the file to the new path
	doc.file_url = file_url

	base_path = frappe.utils.get_site_path()

	if doc.is_private:
		foriginal_file_url = f"{base_path}{original_file_url}"
		ffile_url = f"{base_path}{file_url}"
	else:
		foriginal_file_url = f"{base_path}/public{original_file_url}"
		ffile_url = f"{base_path}/public{file_url}"
	
	shutil.move(foriginal_file_url, ffile_url)

	# save the changes
	try:
		doc.save()
	except Exception as e:
		# rollback the file move
		shutil.move(ffile_url, foriginal_file_url)
	else:
		# update the references fields
		frappe.db.set_value(
			doc.attached_to_doctype,
			doc.attached_to_name,
			doc.attached_to_field,
			doc.file_url,
		)

	if doc.attached_to_field == "pdf_generado":
		frappe.enqueue(
			method="corterra_app.controllers.file.deal_with_diseno",
			doctype=doc.attached_to_doctype,
			name=doc.attached_to_name,
			fieldname="diseno",
			queue="long",
			timeout=1200,
			enqueue_after_commit=True,
		)


def deal_with_diseno(doctype, name, fieldname):
	time.sleep(3) # allow other processes to finish

	if fileid := frappe.db.exists("File", {
		"attached_to_doctype": doctype,
		"attached_to_name": name,
		"attached_to_field": fieldname,
	}):
		file = frappe.get_doc("File", fileid)
		file.run_method("on_update") # trigger the on_update event
