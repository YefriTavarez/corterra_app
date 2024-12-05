# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

import os
import fitz  # PyMuPDF

import frappe
from frappe.utils import get_site_path


__all__ = ("calcular_dimensiones_reales", )

# method = "corterra_app.client.pdf_introspection.calcular_dimensiones_reales"

def puntos_a_pulgadas(valor):
    """Convierte puntos a pulgadas."""
    return valor / 72


@frappe.whitelist()
def calcular_dimensiones_reales(pdf_path: str) -> dict:
    """Calcula las dimensiones reales de los elementos en un PDF."""

    if not pdf_path:
        frappe.throw("No se ha especificado un archivo PDF.")
    
    base_path = get_site_path()
    if pdf_path.startswith("/private"):
        pdf_path = f"{base_path}{pdf_path}"
    elif pdf_path.startswith("/files"):
        pdf_path = f"{base_path}/public{pdf_path}"
    else:
        frappe.throw("No se puede acceder al archivo PDF.")

    if not os.path.exists(pdf_path):
        frappe.throw("El archivo PDF no existe.")

    doc = fitz.open(pdf_path)

    total_min_x, total_min_y = float("inf"), float("inf")
    total_max_x, total_max_y = float("-inf"), float("-inf")

    for page_num, page in enumerate(doc, start=1):
        print(f"\nAnalizando página {page_num}...")

        min_x, min_y = float("inf"), float("inf")
        max_x, max_y = float("-inf"), float("-inf")

        # Dibujos vectoriales
        drawings = page.get_drawings()
        for drawing in drawings:
            for path in drawing["items"]:
                try:
                    coords = []
                    if path[0] == "l" or path[0] == "c" or path[0] == "re":  # Líneas y rectángulos
                        coords = path[1] if isinstance(path[1], list) else [path[1]]
                    elif path[0] == "el":  # Elipses y círculos
                        coords = [path[1].tl, path[1].br]
                    
                    for coord in coords:
                        if hasattr(coord, "x") and hasattr(coord, "y"):  # Manejo de puntos tipo Point
                            x, y = coord.x, coord.y
                            min_x, min_y = min(min_x, x), min(min_y, y)
                            max_x, max_y = max(max_x, x), max(max_y, y)
                except Exception as e:
                    print(f"Error procesando gráfico: {path}, Error: {e}")

        # Imágenes
        for img in page.get_images(full=True):
            xref = img[0]
            try:
                bbox = page.get_image_bbox(xref)
                min_x, min_y = min(min_x, bbox.x0), min(min_y, bbox.y0)
                max_x, max_y = max(max_x, bbox.x1), max(max_y, bbox.y1)
            except Exception as e:
                print(f"Error procesando imagen: {e}")

        # Bloques de texto
        text_blocks = page.get_text("blocks")
        for block in text_blocks:
            x0, y0, x1, y1 = block[:4]
            min_x, min_y = min(min_x, x0), min(min_y, y0)
            max_x, max_y = max(max_x, x1), max(max_y, y1)

        # Actualizar las dimensiones totales
        total_min_x = min(total_min_x, min_x)
        total_min_y = min(total_min_y, min_y)
        total_max_x = max(total_max_x, max_x)
        total_max_y = max(total_max_y, max_y)

        # Dimensiones por página
        # ancho = puntos_a_pulgadas(max_x - min_x)
        # alto = puntos_a_pulgadas(max_y - min_y)
        # print(f"Dimensiones ocupadas en la página {page_num}: Ancho={ancho:.4f}\" x Alto={alto:.4f}\"")

    doc.close()

    # Dimensiones totales
    ancho_total = puntos_a_pulgadas(total_max_x - total_min_x)
    alto_total = puntos_a_pulgadas(total_max_y - total_min_y)
    # print(f"\nTamaño total ocupado por los elementos en el PDF: Ancho={ancho_total:.4f}\" x Alto={alto_total:.4f}\"")

    return {
        "ancho": ancho_total,
        "alto": alto_total
    }
