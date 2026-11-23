from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from cuentas.decorators import solo_clientes, solo_personal
from cuentas.models import Usuario
from core.models import Empresa
from .forms import (
    CambioEstadoTicketForm,
    FiltroTicketForm,
    SeguimientoTicketForm,
    TicketForm,
)
from .models import SeguimientoTicket, Ticket


@solo_clientes
def lista_tickets(request):
    tickets = Ticket.objects.filter(
        empresa__usuario=request.user
    ).select_related("empresa")
    return render(
        request,
        "tickets/lista.html",
        {"tickets": tickets},
    )


@solo_clientes
@require_http_methods(["GET", "POST"])
def nuevo_ticket(request):
    form = TicketForm(
        request.POST if request.method == "POST" else None
    )
    if request.method == "POST" and form.is_valid():
        empresa = get_object_or_404(Empresa, usuario=request.user)
        ticket = form.save(commit=False)
        ticket.empresa = empresa
        ticket.estado = Ticket.Estado.ABIERTO
        ticket.save()
        messages.success(request, "El ticket fue creado correctamente.")
        return redirect("tickets:detalle", id=ticket.id)

    return render(
        request,
        "tickets/nuevo.html",
        {"form": form},
    )


@solo_personal
def gestion_tickets(request):
    form = FiltroTicketForm(request.GET or None)
    tickets = Ticket.objects.select_related("empresa")
    if form.is_bound and form.is_valid() and form.cleaned_data["estado"]:
        tickets = tickets.filter(estado=form.cleaned_data["estado"])
    return render(
        request,
        "tickets/gestion.html",
        {
            "form": form,
            "tickets": tickets,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def detalle_ticket(request, id):
    es_cliente = request.user.rol == Usuario.Rol.CLIENTE
    es_personal = request.user.rol in (
        Usuario.Rol.ADMINISTRADOR,
        Usuario.Rol.TECNICO,
    )
    if es_cliente:
        ticket = get_object_or_404(
            Ticket.objects.select_related("empresa"),
            id=id,
            empresa__usuario=request.user,
        )
    elif es_personal:
        ticket = get_object_or_404(
            Ticket.objects.select_related("empresa"),
            id=id,
        )
    else:
        return HttpResponseForbidden(
            "Esta página está disponible solo para clientes y personal."
        )

    estado_inicial = ticket.estado
    form_mensaje = SeguimientoTicketForm()
    form_estado = CambioEstadoTicketForm(instance=ticket) if es_personal else None

    if request.method == "POST":
        accion = request.POST.get("accion")
        if accion == "mensaje":
            form_mensaje = SeguimientoTicketForm(request.POST)
            if form_mensaje.is_valid():
                seguimiento = form_mensaje.save(commit=False)
                seguimiento.ticket = ticket
                seguimiento.usuario = request.user
                seguimiento.save()
                messages.success(request, "El mensaje fue enviado.")
                return redirect("tickets:detalle", id=ticket.id)
        elif accion == "estado" and es_personal:
            form_estado = CambioEstadoTicketForm(
                request.POST,
                instance=ticket,
            )
            if form_estado.is_valid():
                ticket = form_estado.save(commit=False)
                if ticket.estado == Ticket.Estado.CERRADO:
                    if estado_inicial != Ticket.Estado.CERRADO:
                        ticket.fecha_cierre = timezone.now()
                else:
                    ticket.fecha_cierre = None
                ticket.save(update_fields=["estado", "fecha_cierre"])
                messages.success(request, "El estado del ticket fue actualizado.")
                return redirect("tickets:detalle", id=ticket.id)
        else:
            messages.error(request, "La acción solicitada no es válida.")

    seguimientos = (
        SeguimientoTicket.objects.filter(ticket=ticket)
        .select_related("usuario")
        .order_by("fecha_seguimiento")
    )
    return render(
        request,
        "tickets/detalle.html",
        {
            "ticket": ticket,
            "seguimientos": seguimientos,
            "form_mensaje": form_mensaje,
            "form_estado": form_estado,
            "es_personal": es_personal,
        },
    )
