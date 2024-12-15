# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

from io import BytesIO

from base64 import b64encode
from pyqrcode import create

import frappe


@frappe.whitelist()
def get_svg(link: str, file: str=None) -> bytes:
	"""Get SVG code to display Qrcode for OTP."""

	url = create(link)
	svg = ""
	stream = BytesIO()

	if not file:
		file = stream

	try:
		url.svg(stream, scale=4, background="#eee", module_color="#222")
		svg = stream.getvalue().decode().replace("\n", "")
		svg = b64encode(svg.encode())
	finally:
		if isinstance(file, str):
			with open(file, "wb") as f:
				f.write(stream.getvalue())
		else:
			stream.close()

	return svg


@frappe.whitelist()
def get_qr_link(link: str) -> str:
	"""Saves a the svg file and returns the link to it."""
	
	base = frappe.utils.get_site_path("public", "files")

	filename = f"{frappe.generate_hash()}.svg"

	path = f"{base}/{filename}"

	get_svg(link=link, file=path)

	return f"/files/{filename}"


"""Usage
```JavaScript
frappe.call({
	method: "corterra_app.client.qr.get_qr_link",
	args: {
		link: "https://corterra.do/app/orden-de-produccion/OP-00005?accion=prompt",
	},
	callback: function (r) {
		if (r.message) {
			console.log({ message: r.message });
		}
	},
});
```
"""
