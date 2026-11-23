from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET

from cuentas.decorators import solo_clientes
from cuentas.models import Usuario
from core.models import Empresa, Paquete
from .calculos import calcular_resultado
from .forms import DiagnosticoForm
from .models import Diagnostico, Reporte
from .reportes import generar_pdf_diagnostico, obtener_recomendaciones


CONTROLES = (
    "tiene_antivirus",
    "tiene_respaldo",
    "tiene_contrasenas_2fa",
    "tiene_firewall",
    "tiene_actualizaciones",
    "tiene_politica_escrita",
)


@solo_clientes
def cuestionario(request):
    empresa = get_object_or_404(Empresa, usuario=request.user)
    form = DiagnosticoForm(request.POST if request.method == "POST" else None)

    if request.method == "POST" and form.is_valid():
        respuestas = tuple(
            form.cleaned_data[campo] == DiagnosticoForm.RESPUESTA_SI
            for campo in CONTROLES
        )
        resultado = calcular_resultado(respuestas)
        paquete = Paquete.objects.filter(nombre=resultado["nombre_paquete"]).first()

        if paquete is None:
            form.add_error(
                None,
                (
                    "No está configurado el paquete recomendado. "
                    "Inténtalo más tarde."
                ),
            )
        else:
            diagnostico = Diagnostico.objects.create(
                empresa=empresa,
                paquete_recomendado=paquete,
                indice_proteccion=resultado["indice_proteccion"],
                nivel_riesgo=resultado["nivel_riesgo"],
                **dict(zip(CONTROLES, respuestas)),
            )
            return redirect(
                "diagnostico:resultado",
                id=diagnostico.id,
            )

    return render(
        request,
        "diagnostico/cuestionario.html",
        {"form": form},
    )


@solo_clientes
def resultado(request, id):
    diagnostico = get_object_or_404(
        Diagnostico.objects.select_related("empresa", "paquete_recomendado"),
        id=id,
        empresa__usuario=request.user,
    )
    recomendaciones = obtener_recomendaciones(diagnostico)
    return render(
        request,
        "diagnostico/resultado.html",
        {
            "diagnostico": diagnostico,
            "recomendaciones": recomendaciones,
            "clase_riesgo": f"riesgo-{diagnostico.nivel_riesgo.lower()}",
        },
    )


@login_required
@require_GET
def reporte_pdf(request, id):
    diagnostico = get_object_or_404(
        Diagnostico.objects.select_related(
            "empresa",
            "empresa__usuario",
            "paquete_recomendado",
        ),
        id=id,
    )
    es_administrador = request.user.rol == Usuario.Rol.ADMINISTRADOR
    es_dueno = diagnostico.empresa.usuario_id == request.user.id
    if not es_administrador and not es_dueno:
        raise Http404

    recomendaciones = obtener_recomendaciones(diagnostico)
    resumen = (
        " ".join(recomendaciones)
        if recomendaciones
        else "No hay controles pendientes según las respuestas recibidas."
    )
    contenido_pdf = generar_pdf_diagnostico(diagnostico)
    Reporte.objects.create(
        diagnostico=diagnostico,
        ruta_archivo="generado bajo demanda",
        resumen=resumen,
    )

    respuesta = HttpResponse(contenido_pdf, content_type="application/pdf")
    respuesta["Content-Disposition"] = (
        f'attachment; filename="diagnostico-{diagnostico.id}.pdf"'
    )
    return respuesta
