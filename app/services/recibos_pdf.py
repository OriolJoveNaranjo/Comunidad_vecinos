from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    HRFlowable,
)

from app.models import Recibo


def generar_recibo_pdf(recibo: Recibo) -> bytes:
    buffer = BytesIO()

    documento = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=f"Recibo {recibo.numero}",
        author="Gestión Comunidad de Vecinos",
    )

    estilos = getSampleStyleSheet()

    estilos.add(
        ParagraphStyle(
            name="ImporteRecibo",
            parent=estilos["Heading1"],
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#1565C0"),
        )
    )

    contenido = []

    def campo(etiqueta: str, valor):
        texto = escape(str(valor))
        contenido.append(
            Paragraph(
                f"<b>{escape(etiqueta)}:</b> {texto}",
                estilos["Normal"],
            )
        )
        contenido.append(Spacer(1, 0.25 * cm))

    contenido.append(
        Paragraph(
            "Gestión Comunidad de Vecinos",
            estilos["Title"],
        )
    )
    contenido.append(
        Paragraph("Justificante de pago", estilos["Heading2"])
    )
    contenido.append(
        HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor("#1565C0"),
        )
    )
    contenido.append(Spacer(1, 0.6 * cm))

    campo("Número de recibo", recibo.numero)
    campo(
        "Fecha de emisión (UTC)",
        recibo.fecha_emision.strftime("%d/%m/%Y"),
    )
    campo("Identificador del pago", recibo.pago_id)

    contenido.append(Spacer(1, 0.4 * cm))
    contenido.append(
        Paragraph("Datos del vecino", estilos["Heading2"])
    )

    campo("Nombre", f"{recibo.nombre} {recibo.apellido}")
    campo("Piso", recibo.piso)
    campo("Puerta", recibo.puerta)

    contenido.append(Spacer(1, 0.4 * cm))
    contenido.append(
        Paragraph("Detalle del pago", estilos["Heading2"])
    )

    metodos = {
        "transferencia": "Transferencia bancaria",
        "efectivo": "Efectivo",
        "domiciliacion": "Domiciliación bancaria",
    }

    campo("Concepto", recibo.concepto)
    campo("Fecha del pago", recibo.fecha_pago.strftime("%d/%m/%Y"))
    campo(
        "Método de pago",
        metodos.get(recibo.metodo_pago, recibo.metodo_pago),
    )

    importe = (
        f"{recibo.importe:,.2f}"
        .replace(",", "_")
        .replace(".", ",")
        .replace("_", ".")
    )

    contenido.append(Spacer(1, 0.6 * cm))
    contenido.append(
        Paragraph(
            f"Importe recibido: {importe} €",
            estilos["ImporteRecibo"],
        )
    )
    contenido.append(Spacer(1, 0.6 * cm))
    contenido.append(
        Paragraph(
            "Este justificante corresponde al pago indicado. "
            "El importe recibido puede ser un pago parcial de la cuota.",
            estilos["Normal"],
        )
    )

    documento.build(contenido)
    return buffer.getvalue()