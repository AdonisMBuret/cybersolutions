import csv
import secrets
import string
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
from io import StringIO

from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from cuentas.decorators import solo_clientes, solo_personal
from cuentas.models import Usuario
from diagnostico.models import Diagnostico
from tickets.models import Ticket
from .forms import (
    FiltroPanelAdminForm,
    PagoSimuladoForm,
    SolicitudContratoForm,
)
from .models import Contrato, Empresa, Paquete, Pago


DESCUENTOS_CONTRATO = {
    Contrato.TipoContrato.MENSUAL: Decimal("0"),
    Contrato.TipoContrato.TRIMESTRAL: Decimal("0.05"),
    Contrato.TipoContrato.ANUAL: Decimal("0.10"),
}

DURACION_CONTRATO_DIAS = {
    Contrato.TipoContrato.MENSUAL: 30,
    Contrato.TipoContrato.TRIMESTRAL: 90,
    Contrato.TipoContrato.ANUAL: 365,
}


def _convertir_id(valor):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def _render_catalogo(request, form=None):
    paquetes = list(
        Paquete.objects.filter(estado=Paquete.Estado.ACTIVO).order_by(
            "precio_mensual"
        )
    )
    ids_paquetes = {paquete.id for paquete in paquetes}
    recomendado_id = _convertir_id(request.GET.get("recomendado"))
    if recomendado_id not in ids_paquetes:
        recomendado_id = None

    es_cliente = (
        request.user.is_authenticated
        and request.user.rol == Usuario.Rol.CLIENTE
    )
    if form is None and es_cliente:
        paquete_inicial = recomendado_id
        if paquete_inicial is None and paquetes:
            paquete_inicial = paquetes[0].id
        form = SolicitudContratoForm(
            initial={"paquete": paquete_inicial} if paquete_inicial else None
        )

    seleccionado_id = None
    if form is not None:
        seleccionado_id = _convertir_id(form["paquete"].value())

    return render(
        request,
        "core/paquetes.html",
        {
            "paquetes": paquetes,
            "recomendado_id": recomendado_id,
            "seleccionado_id": seleccionado_id,
            "form": form,
        },
    )


def inicio(request):
    paquetes = Paquete.objects.filter(estado=Paquete.Estado.ACTIVO).order_by(
        "precio_mensual"
    )
    return render(request, "core/inicio.html", {"paquetes": paquetes})


@require_http_methods(["GET", "POST"])
def paquetes(request):
    if request.method == "POST":
        return _solicitar_contrato(request)
    return _render_catalogo(request)


@solo_clientes
@require_POST
def _solicitar_contrato(request):
    form = SolicitudContratoForm(request.POST)
    if not form.is_valid():
        return _render_catalogo(request, form=form)

    empresa = get_object_or_404(Empresa, usuario=request.user)
    paquete = form.cleaned_data["paquete"]
    tipo_contrato = form.cleaned_data["tipo_contrato"]
    descuento = DESCUENTOS_CONTRATO[tipo_contrato]
    precio_acordado = (
        paquete.precio_mensual * (Decimal("1") - descuento)
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    contrato = Contrato.objects.create(
        empresa=empresa,
        paquete=paquete,
        tipo_contrato=tipo_contrato,
        precio_acordado=precio_acordado,
    )
    return redirect("core:pago", id=contrato.id)


@solo_clientes
@require_http_methods(["GET", "POST"])
def pago(request, id):
    contrato = get_object_or_404(
        Contrato.objects.select_related("empresa", "paquete"),
        id=id,
        empresa__usuario=request.user,
        estado=Contrato.Estado.SOLICITADO,
    )
    form = PagoSimuladoForm(request.POST if request.method == "POST" else None)

    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            contrato = get_object_or_404(
                Contrato.objects.select_for_update().select_related("paquete"),
                id=id,
                empresa__usuario=request.user,
                estado=Contrato.Estado.SOLICITADO,
            )
            fecha_inicio = timezone.localdate()
            fecha_fin = fecha_inicio + timedelta(
                days=DURACION_CONTRATO_DIAS[contrato.tipo_contrato]
            )
            referencia = "".join(
                secrets.choice(string.ascii_uppercase + string.digits)
                for _ in range(10)
            )
            Pago.objects.create(
                contrato=contrato,
                monto=contrato.precio_acordado,
                metodo_pago=form.cleaned_data["metodo_pago"],
                referencia=referencia,
                estado=Pago.Estado.PAGADO,
            )
            contrato.estado = Contrato.Estado.ACTIVO
            contrato.fecha_inicio = fecha_inicio
            contrato.fecha_fin = fecha_fin
            contrato.save(
                update_fields=["estado", "fecha_inicio", "fecha_fin"]
            )

        messages.success(
            request,
            "Pago confirmado. Tu contrato está activo.",
        )
        return redirect("/panel/")

    return render(
        request,
        "core/pago.html",
        {
            "contrato": contrato,
            "form": form,
        },
    )


@solo_clientes
def panel_cliente(request):
    empresa = get_object_or_404(Empresa, usuario=request.user)
    ultimo_diagnostico = (
        Diagnostico.objects.filter(empresa=empresa)
        .order_by("-fecha_diagnostico")
        .first()
    )
    contrato_activo = (
        Contrato.objects.filter(
            empresa=empresa,
            estado=Contrato.Estado.ACTIVO,
        )
        .select_related("paquete")
        .order_by("-fecha_inicio", "-fecha_solicitud")
        .first()
    )
    tickets_abiertos = Ticket.objects.filter(
        empresa=empresa,
        estado=Ticket.Estado.ABIERTO,
    ).count()
    ultimos_tickets = (
        Ticket.objects.filter(empresa=empresa)
        .order_by("-fecha_creacion")[:3]
    )

    return render(
        request,
        "core/panel_cliente.html",
        {
            "empresa": empresa,
            "ultimo_diagnostico": ultimo_diagnostico,
            "contrato_activo": contrato_activo,
            "tickets_abiertos": tickets_abiertos,
            "ultimos_tickets": ultimos_tickets,
        },
    )


def _exportar_contratos_csv(contratos):
    salida = StringIO(newline="")
    escritor = csv.writer(salida)
    escritor.writerow(["Cliente", "Paquete", "Tipo", "Estado", "Vence"])
    for contrato in contratos:
        vence = (
            contrato.fecha_fin.strftime("%d/%m/%Y")
            if contrato.fecha_fin
            else ""
        )
        escritor.writerow(
            [
                contrato.empresa.nombre_comercial,
                contrato.paquete.nombre,
                contrato.get_tipo_contrato_display(),
                contrato.get_estado_display(),
                vence,
            ]
        )

    respuesta = HttpResponse(
        salida.getvalue().encode("utf-8-sig"),
        content_type="text/csv",
    )
    respuesta["Content-Disposition"] = 'attachment; filename="contratos.csv"'
    return respuesta


@solo_personal
def panel_administrador(request):
    form = FiltroPanelAdminForm(request.GET or None)
    contratos = Contrato.objects.select_related("empresa", "paquete")
    formulario_valido = form.is_valid() if form.is_bound else True

    if form.is_bound and formulario_valido:
        nombre_empresa = form.cleaned_data["q"].strip()
        estado = form.cleaned_data["estado"]
        if nombre_empresa:
            contratos = contratos.filter(
                empresa__nombre_comercial__icontains=nombre_empresa
            )
        if estado:
            contratos = contratos.filter(estado=estado)

    if request.GET.get("exportar") == "csv" and formulario_valido:
        return _exportar_contratos_csv(contratos)

    mes_actual = timezone.localdate()
    ingresos_mes = (
        Pago.objects.filter(
            estado=Pago.Estado.PAGADO,
            fecha_pago__year=mes_actual.year,
            fecha_pago__month=mes_actual.month,
        ).aggregate(total=Sum("monto"))["total"]
        or Decimal("0.00")
    )
    return render(
        request,
        "core/panel_administrador.html",
        {
            "form": form,
            "contratos": contratos,
            "clientes_activos": (
                Contrato.objects.filter(estado=Contrato.Estado.ACTIVO)
                .values("empresa_id")
                .distinct()
                .count()
            ),
            "contratos_vigentes": Contrato.objects.filter(
                estado=Contrato.Estado.ACTIVO
            ).count(),
            "tickets_abiertos": Ticket.objects.filter(
                estado=Ticket.Estado.ABIERTO
            ).count(),
            "ingresos_mes": ingresos_mes,
        },
    )
