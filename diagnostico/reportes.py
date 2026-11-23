from html import escape
from io import BytesIO

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


COLOR_PRIMARIO = colors.HexColor("#A42526")
COLOR_FONDO_SUAVE = colors.HexColor("#FBEFEF")

CONTROLES_DIAGNOSTICO = (
    ("tiene_antivirus", "Antivirus en los equipos"),
    ("tiene_respaldo", "Copias de respaldo"),
    ("tiene_contrasenas_2fa", "Contraseñas seguras y doble autenticación"),
    ("tiene_firewall", "Firewall o protección de red"),
    ("tiene_actualizaciones", "Actualizaciones periódicas"),
    ("tiene_politica_escrita", "Política de seguridad por escrito"),
)

RECOMENDACIONES = {
    "tiene_antivirus": "Instale y mantenga actualizado un antivirus en todos los equipos.",
    "tiene_respaldo": "Active copias de respaldo automáticas de la información.",
    "tiene_contrasenas_2fa": "Use contraseñas seguras y active la doble autenticación.",
    "tiene_firewall": "Active un firewall para proteger la red de la empresa.",
    "tiene_actualizaciones": "Instale las actualizaciones periódicas de sus equipos y programas.",
    "tiene_politica_escrita": "Prepare una política de seguridad por escrito para su empresa.",
}


def obtener_recomendaciones(diagnostico):
    return [
        RECOMENDACIONES[campo]
        for campo, _ in CONTROLES_DIAGNOSTICO
        if not getattr(diagnostico, campo)
    ]


def _crear_encabezado_y_pie(canvas, documento):
    ancho, alto = letter
    canvas.saveState()
    canvas.setFillColor(COLOR_PRIMARIO)
    canvas.rect(0, alto - 0.8 * inch, ancho, 0.8 * inch, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 15)
    canvas.drawString(
        documento.leftMargin,
        alto - 0.51 * inch,
        "Cyber Solutions RD · Reporte de diagnóstico",
    )
    canvas.setFillColor(colors.HexColor("#262626"))
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(
        ancho / 2,
        0.35 * inch,
        "Documento confidencial · Ley núm. 172-13",
    )
    canvas.restoreState()


def generar_pdf_diagnostico(diagnostico):
    archivo = BytesIO()
    documento = SimpleDocTemplate(
        archivo,
        pagesize=letter,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=1.05 * inch,
        bottomMargin=0.65 * inch,
        title="Reporte de diagnóstico",
        author="Cyber Solutions RD",
    )
    estilos = getSampleStyleSheet()
    estilo_seccion = ParagraphStyle(
        "SeccionDiagnostico",
        parent=estilos["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        spaceBefore=8,
        spaceAfter=7,
        textColor=colors.HexColor("#262626"),
    )
    estilo_normal = ParagraphStyle(
        "TextoDiagnostico",
        parent=estilos["BodyText"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#262626"),
    )
    estilo_centrado = ParagraphStyle(
        "DatoCentrado",
        parent=estilo_normal,
        alignment=TA_CENTER,
    )
    historia = []

    fecha = timezone.localtime(diagnostico.fecha_diagnostico).strftime(
        "%d/%m/%Y %H:%M"
    )
    datos_empresa = (
        f"<b>Empresa:</b> {escape(diagnostico.empresa.nombre_comercial)}<br/>"
        f"<b>Sector:</b> {escape(diagnostico.empresa.get_sector_display())}<br/>"
        f"<b>Tamaño:</b> {escape(diagnostico.empresa.get_tamano_display())}<br/>"
        f"<b>Fecha:</b> {escape(fecha)}"
    )
    historia.append(Paragraph(datos_empresa, estilo_normal))
    historia.append(Spacer(1, 12))

    paquete = diagnostico.paquete_recomendado
    if paquete is None:
        nombre_paquete = "No disponible"
        precio_paquete = "No disponible"
    else:
        nombre_paquete = escape(paquete.nombre)
        precio_paquete = f"RD$ {paquete.precio_mensual:,.2f} / mes"

    resumen = Table(
        [
            [
                Paragraph("<b>Índice de protección</b>", estilo_centrado),
                Paragraph("<b>Nivel de riesgo</b>", estilo_centrado),
                Paragraph("<b>Paquete recomendado</b>", estilo_centrado),
            ],
            [
                Paragraph(
                    f"<font size='20'><b>{diagnostico.indice_proteccion} / 6</b></font>",
                    estilo_centrado,
                ),
                Paragraph(
                    f"<font size='14'><b>{escape(diagnostico.nivel_riesgo)}</b></font>",
                    estilo_centrado,
                ),
                Paragraph(
                    f"<b>{nombre_paquete}</b><br/>{escape(precio_paquete)}",
                    estilo_centrado,
                ),
            ],
        ],
        colWidths=[2.34 * inch, 2.34 * inch, 2.34 * inch],
    )
    resumen.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_FONDO_SUAVE),
                ("BOX", (0, 0), (-1, -1), 1.5, COLOR_PRIMARIO),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    historia.append(resumen)
    historia.append(Paragraph("Controles de seguridad", estilo_seccion))

    filas_controles = [
        [
            Paragraph("<b>Control</b>", estilo_normal),
            Paragraph("<b>Respuesta</b>", estilo_centrado),
        ]
    ]
    respuestas = []
    for campo, nombre in CONTROLES_DIAGNOSTICO:
        respuesta = bool(getattr(diagnostico, campo))
        respuestas.append(respuesta)
        filas_controles.append(
            [
                Paragraph(escape(nombre), estilo_normal),
                Paragraph(
                    "<b>Sí</b>" if respuesta else "<b>No</b>",
                    estilo_centrado,
                ),
            ]
        )

    tabla_controles = Table(
        filas_controles,
        colWidths=[5.7 * inch, 1.32 * inch],
        repeatRows=1,
    )
    estilos_tabla = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEEEEE")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]
    for indice, respuesta in enumerate(respuestas, start=1):
        estilos_tabla.append(
            (
                "TEXTCOLOR",
                (1, indice),
                (1, indice),
                colors.HexColor("#198754" if respuesta else "#A42526"),
            )
        )
    tabla_controles.setStyle(TableStyle(estilos_tabla))
    historia.append(tabla_controles)
    historia.append(Paragraph("Recomendaciones", estilo_seccion))

    recomendaciones = obtener_recomendaciones(diagnostico)
    if recomendaciones:
        historia.append(
            ListFlowable(
                [
                    ListItem(
                        Paragraph(escape(recomendacion), estilo_normal),
                        leftIndent=12,
                    )
                    for recomendacion in recomendaciones
                ],
                bulletType="bullet",
                leftIndent=18,
                bulletFontName="Helvetica",
                bulletFontSize=8,
                bulletColor=COLOR_PRIMARIO,
            )
        )
    else:
        historia.append(
            Paragraph(
                "No hay controles pendientes según las respuestas recibidas.",
                estilo_normal,
            )
        )

    documento.build(
        historia,
        onFirstPage=_crear_encabezado_y_pie,
        onLaterPages=_crear_encabezado_y_pie,
    )
    return archivo.getvalue()
