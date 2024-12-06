# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

import os
import math

import fitz  # PyMuPDF

import frappe
from frappe.model import naming

__all__ = ("agregar_bounding_boxes", )

# method = "corterra_app.client.pdf_manipulator.agregar_bounding_boxes"

DEBUG = False


def puntos_a_pulgadas(valor):
    """Convierte puntos a pulgadas."""
    return valor / 72


def pulgadas_a_puntos(valor):
    """Convierte pulgadas a puntos."""
    return valor * 72


def calcular_siguiente_multiplo(valor, multiplo=6):
    """Calcula el siguiente múltiplo de 6 pulgadas."""
    siguiente = math.ceil(valor / multiplo) * multiplo
    if siguiente - valor < 1:  # Si la diferencia es menor a 1 pulgada
        siguiente += multiplo
    return siguiente


@frappe.whitelist()
def agregar_bounding_boxes(pdf_path: str, output_path: str = None):
    """Agrega bounding boxes a un PDF."""

    if not pdf_path.endswith(".pdf"):
        frappe.throw("El archivo PDF no tiene la extensión correcta.")

    if not pdf_path:
        frappe.throw("No se ha especificado un archivo PDF.")

    base_path = frappe.utils.get_site_path()
    if pdf_path.startswith("/private"):
        pdf_path = f"{base_path}{pdf_path}"
    elif pdf_path.startswith("/files"):
        pdf_path = f"{base_path}/public{pdf_path}"
    else:
        frappe.throw("No se puede acceder al archivo PDF.")

    if output_path:       
        if not output_path.endswith(".pdf"):
            frappe.throw("El archivo de salida no tiene la extensión correcta.")

        if output_path.startswith("/private"):
            output_path = f"{base_path}{output_path}"
        elif output_path.startswith("/files"):
            output_path = f"{base_path}/public{output_path}"
        else:
            frappe.throw("No se puede acceder al archivo de salida.")
        
        if not os.path.exists(output_path):
            frappe.throw("No se puede acceder al archivo de salida.")
    else:
        filename = get_pdf_output_name()
        # output_path = f"/private/files/{filename}"
        output_path = f"{base_path}/public/files/{filename}"
        frappe.utils.touch_file(output_path)
        
    if not os.path.exists(pdf_path):
        frappe.throw("El archivo PDF no existe.")

    doc = fitz.open(pdf_path)
    output_pdf = fitz.open()  # Crear un nuevo documento PDF

    for page_num, page in enumerate(doc, start=1):
        if DEBUG:
            print(f"\nAnalizando y anotando página {page_num}...")

        min_x, min_y = float("inf"), float("inf")
        max_x, max_y = float("-inf"), float("-inf")

        # Detectar los elementos gráficos
        drawings = page.get_drawings()
        for drawing in drawings:
            for path in drawing["items"]:
                try:
                    if path[0] in ["l", "c", "re"]:  # Líneas, curvas y rectángulos
                        coords = path[1]
                        if isinstance(coords, list):
                            for x, y in coords:
                                min_x, min_y = min(min_x, x), min(min_y, y)
                                max_x, max_y = max(max_x, x), max(max_y, y)
                        elif hasattr(coords, "x") and hasattr(coords, "y"):
                            x, y = coords.x, coords.y
                            min_x, min_y = min(min_x, x), min(min_y, y)
                            max_x, max_y = max(max_x, x), max(max_y, y)
                except Exception as e:
                    if DEBUG:
                        print(f"Error procesando gráfico: {path}, Error: {e}")

        # Textos y bloques
        text_blocks = page.get_text("blocks")
        for block in text_blocks:
            x0, y0, x1, y1 = block[:4]
            min_x, min_y = min(min_x, x0), min(min_y, y0)
            max_x, max_y = max(max_x, x1), max(max_y, y1)

        # Verificar si hay elementos válidos
        if min_x >= max_x or min_y >= max_y:
            if DEBUG:
                print(f"No se encontraron elementos válidos en la página {page_num}.")

            continue

        # Crear Bounding Box Azul
        rect_azul = fitz.Rect(min_x, min_y, max_x, max_y)
        ancho_azul = puntos_a_pulgadas(max_x - min_x)
        alto_azul = puntos_a_pulgadas(max_y - min_y)

        # Calcular Bounding Box Naranja
        ancho_naranja = calcular_siguiente_multiplo(ancho_azul)
        alto_naranja = calcular_siguiente_multiplo(alto_azul)
        ancho_naranja_puntos = pulgadas_a_puntos(ancho_naranja)
        alto_naranja_puntos = pulgadas_a_puntos(alto_naranja)

        # Crear nueva página del tamaño del Bounding Box Naranja
        nuevo_ancho = ancho_naranja_puntos + 4  # +1 punto para visibilidad
        nuevo_alto = alto_naranja_puntos + 4  # +1 punto para visibilidad
        nueva_pagina = output_pdf.new_page(width=nuevo_ancho, height=nuevo_alto)

        # Calcular rectángulo naranja centrado
        offset_naranja_x = (nuevo_ancho - ancho_naranja_puntos) / 2
        offset_naranja_y = (nuevo_alto - alto_naranja_puntos) / 2

        # offset_naranja_x = (nuevo_ancho - ancho_naranja_puntos) / 2 - 0.5
        # offset_naranja_y = (nuevo_alto - alto_naranja_puntos) / 2 - 0.5
        rect_naranja = fitz.Rect(
            offset_naranja_x,
            offset_naranja_y,
            offset_naranja_x + ancho_naranja_puntos,
            offset_naranja_y + alto_naranja_puntos
        )

        # Centrar Bounding Box Azul dentro del Naranja
        offset_azul_x = (rect_naranja.width - rect_azul.width) / 2
        offset_azul_y = (rect_naranja.height - rect_azul.height) / 2

        rect_azul_centrado = fitz.Rect(
            rect_naranja.x0 + offset_azul_x,
            rect_naranja.y0 + offset_azul_y,
            rect_naranja.x0 + offset_azul_x + rect_azul.width,
            rect_naranja.y0 + offset_azul_y + rect_azul.height
        )

        # Transferir contenido original centrado en el Bounding Box Azul
        nueva_pagina.show_pdf_page(
            rect=rect_azul_centrado,
            src=doc,
            pno=page_num - 1,
            clip=rect_azul
        )

        # Dibujar los rectángulos (después de transferir el contenido)
        nueva_pagina.draw_rect(rect_naranja, color=(1, 0.5, 0), width=2.0)  # Naranja
        nueva_pagina.draw_rect(rect_azul_centrado, color=(0.5, 0.8, 1), width=1.0)  # Azul

        if DEBUG:
            print(f"Bounding box azul centrado: Ancho={ancho_azul:.3f}\" x Alto={alto_azul:.3f}\"")
            print(f"Bounding box naranja: Ancho={ancho_naranja}\" x Alto={alto_naranja}\"")
            print(f"Tamaño final del PDF: {puntos_a_pulgadas(nuevo_ancho):.3f}\" x {puntos_a_pulgadas(nuevo_alto):.3f}\"")


    # Guardar el archivo
    output_pdf.save(output_path)
    output_pdf.close()
    doc.close()

    if DEBUG:
        print(f"\nArchivo anotado guardado en: {output_path}")

    return output_path \
        .replace(f"{base_path}/public", "")


def get_pdf_output_name():
    """Genera un nombre de archivo para el PDF de salida."""
    seq = naming.make_autoname(".YY.MM.DD.##")

    return f"{seq}.pdf"


if __name__ == "__main__":
    pdf_path = "plano_caja.pdf"
    agregar_bounding_boxes(pdf_path)
