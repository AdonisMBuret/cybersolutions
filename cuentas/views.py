from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.views import redirect_to_login
from django.db import IntegrityError, transaction
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST, require_http_methods

from core.models import Empresa
from .forms import AccesoForm, RegistroForm
from .models import Usuario


def _ruta_segun_rol(usuario):
    if usuario.rol in (Usuario.Rol.ADMINISTRADOR, Usuario.Rol.TECNICO):
        return "/panel-admin/"
    return "/panel/"


@require_http_methods(["GET", "POST"])
def acceso(request):
    if request.user.is_authenticated:
        return redirect(_ruta_segun_rol(request.user))

    form = AccesoForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        usuario = authenticate(
            request,
            email=form.cleaned_data["email"],
            password=form.cleaned_data["password"],
        )
        if usuario is None:
            form.add_error(
                None,
                "El correo electrónico o la contraseña no son correctos.",
            )
        else:
            login(request, usuario)
            return redirect(_ruta_segun_rol(usuario))

    return render(request, "cuentas/acceso.html", {"form": form})


@require_http_methods(["GET", "POST"])
def registro(request):
    if request.user.is_authenticated:
        return redirect(_ruta_segun_rol(request.user))

    form = RegistroForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        datos = form.cleaned_data
        try:
            with transaction.atomic():
                usuario = Usuario.objects.create_user(
                    email=datos["email"],
                    password=datos["password"],
                    rol=Usuario.Rol.CLIENTE,
                )
                Empresa.objects.create(
                    usuario=usuario,
                    nombre_comercial=datos["nombre_comercial"],
                    sector=datos["sector"],
                    tamano=datos["tamano"],
                    cantidad_empleados=datos["cantidad_empleados"],
                    cantidad_equipos=datos["cantidad_equipos"],
                    telefono=datos["telefono"],
                    direccion=datos["direccion"],
                )
        except IntegrityError:
            if Usuario.objects.filter(email__iexact=datos["email"]).exists():
                form.add_error(
                    "email",
                    "Ya existe una cuenta registrada con este correo electrónico.",
                )
            else:
                raise
        else:
            login(request, usuario)
            return redirect("/diagnostico/")

    return render(request, "cuentas/registro.html", {"form": form})


@require_POST
def salir(request):
    logout(request)
    messages.info(request, "Has cerrado sesión.")
    return redirect("/")


def solo_administradores(view_func):
    @wraps(view_func)
    def vista_protegida(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(
                request.get_full_path(),
                settings.LOGIN_URL,
            )
        if request.user.rol != Usuario.Rol.ADMINISTRADOR:
            return HttpResponseForbidden(
                "No tienes permiso para acceder a esta página."
            )
        return view_func(request, *args, **kwargs)

    return vista_protegida
