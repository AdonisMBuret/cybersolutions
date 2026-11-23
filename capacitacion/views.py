from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from cuentas.decorators import solo_clientes
from .forms import SimulacroForm
from .models import Leccion, ProgresoLeccion


CORREOS_SIMULACRO = (
    {
        "id": 1,
        "remitente": "avisos@seguridad-cuenta.example",
        "asunto": "Tu cuenta será suspendida hoy",
        "contenido": (
            "Para evitar la suspensión, responde a este correo con tu "
            "contraseña. La solicitud es urgente."
        ),
        "es_fraude": True,
        "explicacion": "Un servicio legítimo no debe pedirte la contraseña por correo.",
    },
    {
        "id": 2,
        "remitente": "avisos@servicio-ejemplo.example",
        "asunto": "Tu estado de cuenta está disponible",
        "contenido": (
            "Puedes consultar tu estado de cuenta desde la aplicación que ya "
            "usas. Nunca envíes tus claves en respuesta a este mensaje."
        ),
        "es_fraude": False,
        "explicacion": "El mensaje dirige a la aplicación habitual y no pide datos secretos.",
    },
    {
        "id": 3,
        "remitente": "premios@regalo-sorpresa.example",
        "asunto": "Ganaste un premio: confirma tus datos",
        "contenido": (
            "Para recibir un premio que no solicitaste, envía una copia de tu "
            "documento y paga un cargo de entrega hoy."
        ),
        "es_fraude": True,
        "explicacion": "Un premio inesperado que pide documentos y dinero es una señal de fraude.",
    },
    {
        "id": 4,
        "remitente": "soporte@empresa-ejemplo.example",
        "asunto": "Mantenimiento programado para el sábado",
        "contenido": (
            "El sistema tendrá mantenimiento el sábado de 8:00 a 9:00 p. m. "
            "Puedes revisar el aviso en el portal interno habitual."
        ),
        "es_fraude": False,
        "explicacion": "El aviso usa un canal interno conocido y no solicita información privada.",
    },
    {
        "id": 5,
        "remitente": "gerencia@empresa-ejemplo.example",
        "asunto": "Haz esta transferencia sin consultar",
        "contenido": (
            "Necesito que transfieras dinero a una cuenta nueva de inmediato. "
            "No llames para confirmar porque estoy en una reunión."
        ),
        "es_fraude": True,
        "explicacion": "Una solicitud urgente de dinero debe confirmarse por otro canal conocido.",
    },
)

CLASES_ESTADO = {
    ProgresoLeccion.Estado.PENDIENTE: "pendiente",
    ProgresoLeccion.Estado.EN_CURSO: "en-curso",
    ProgresoLeccion.Estado.COMPLETADA: "completada",
}


@solo_clientes
def lista_lecciones(request):
    lecciones = list(
        Leccion.objects.filter(estado=Leccion.Estado.ACTIVA).order_by("orden")
    )
    progresos = {
        progreso.leccion_id: progreso
        for progreso in ProgresoLeccion.objects.filter(
            usuario=request.user,
            leccion__in=lecciones,
        )
    }

    actividades = []
    completadas = 0
    for leccion in lecciones:
        progreso = progresos.get(leccion.id)
        estado = (
            progreso.estado
            if progreso is not None
            else ProgresoLeccion.Estado.PENDIENTE
        )
        if estado == ProgresoLeccion.Estado.COMPLETADA:
            completadas += 1
        actividades.append(
            {
                "leccion": leccion,
                "estado": estado,
                "estado_texto": dict(ProgresoLeccion.Estado.choices)[estado],
                "clase_estado": CLASES_ESTADO[estado],
                "puntaje": progreso.puntaje if progreso is not None else None,
            }
        )

    total = len(lecciones)
    porcentaje = round(completadas * 100 / total) if total else 0
    return render(
        request,
        "capacitacion/lista.html",
        {
            "actividades": actividades,
            "completadas": completadas,
            "total": total,
            "porcentaje": porcentaje,
        },
    )


@solo_clientes
@require_http_methods(["GET", "POST"])
def leccion(request, id):
    leccion = get_object_or_404(
        Leccion,
        id=id,
        estado=Leccion.Estado.ACTIVA,
    )
    if leccion.tipo == Leccion.Tipo.SIMULACRO:
        return redirect("capacitacion:simulacro", id=leccion.id)

    if request.method == "POST":
        ahora = timezone.now()
        progreso, creado = ProgresoLeccion.objects.get_or_create(
            usuario=request.user,
            leccion=leccion,
            defaults={
                "estado": ProgresoLeccion.Estado.COMPLETADA,
                "fecha_completada": ahora,
            },
        )
        if not creado and progreso.estado != ProgresoLeccion.Estado.COMPLETADA:
            progreso.estado = ProgresoLeccion.Estado.COMPLETADA
            progreso.fecha_completada = ahora
            progreso.save(update_fields=["estado", "fecha_completada"])
        messages.success(request, "La lección quedó marcada como completada.")
        return redirect("capacitacion:leccion", id=leccion.id)

    progreso, creado = ProgresoLeccion.objects.get_or_create(
        usuario=request.user,
        leccion=leccion,
        defaults={"estado": ProgresoLeccion.Estado.EN_CURSO},
    )
    if not creado and progreso.estado == ProgresoLeccion.Estado.PENDIENTE:
        progreso.estado = ProgresoLeccion.Estado.EN_CURSO
        progreso.save(update_fields=["estado"])

    return render(
        request,
        "capacitacion/leccion.html",
        {
            "leccion": leccion,
            "progreso": progreso,
        },
    )


@solo_clientes
@require_http_methods(["GET", "POST"])
def simulacro(request, id):
    leccion = get_object_or_404(
        Leccion,
        id=id,
        tipo=Leccion.Tipo.SIMULACRO,
        estado=Leccion.Estado.ACTIVA,
    )
    progreso, creado = ProgresoLeccion.objects.get_or_create(
        usuario=request.user,
        leccion=leccion,
        defaults={"estado": ProgresoLeccion.Estado.EN_CURSO},
    )
    if not creado and progreso.estado == ProgresoLeccion.Estado.PENDIENTE:
        progreso.estado = ProgresoLeccion.Estado.EN_CURSO
        progreso.save(update_fields=["estado"])

    form = SimulacroForm(
        CORREOS_SIMULACRO,
        request.POST if request.method == "POST" else None,
    )
    if request.method == "POST" and form.is_valid():
        correos_resultado = []
        aciertos = 0
        for correo in CORREOS_SIMULACRO:
            respuesta_usuario = (
                form.cleaned_data[f"correo_{correo['id']}"]
                == SimulacroForm.RESPUESTA_SI
            )
            es_correcta = respuesta_usuario == correo["es_fraude"]
            if es_correcta:
                aciertos += 1
            correos_resultado.append(
                {
                    **correo,
                    "respuesta_usuario": "Sí" if respuesta_usuario else "No",
                    "respuesta_correcta": (
                        "Sí" if correo["es_fraude"] else "No"
                    ),
                    "es_correcta": es_correcta,
                }
            )

        puntaje = round(aciertos * 100 / len(CORREOS_SIMULACRO))
        progreso.estado = ProgresoLeccion.Estado.COMPLETADA
        progreso.puntaje = puntaje
        progreso.fecha_completada = timezone.now()
        progreso.save(
            update_fields=["estado", "puntaje", "fecha_completada"]
        )
        return render(
            request,
            "capacitacion/simulacro.html",
            {
                "leccion": leccion,
                "form": form,
                "correos": correos_resultado,
                "resultado": True,
                "puntaje": puntaje,
            },
        )

    correos = [
        {
            **correo,
            "campo_form": form[f"correo_{correo['id']}"],
        }
        for correo in CORREOS_SIMULACRO
    ]
    puntaje_anterior = (
        progreso.puntaje
        if progreso.estado == ProgresoLeccion.Estado.COMPLETADA
        else None
    )
    return render(
        request,
        "capacitacion/simulacro.html",
        {
            "leccion": leccion,
            "form": form,
            "correos": correos,
            "resultado": False,
            "puntaje_anterior": puntaje_anterior,
        },
    )
