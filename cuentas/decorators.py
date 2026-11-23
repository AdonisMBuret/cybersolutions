from functools import wraps

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

from .models import Usuario


def solo_clientes(view_func):
    @wraps(view_func)
    @login_required
    def vista_protegida(request, *args, **kwargs):
        if request.user.rol != Usuario.Rol.CLIENTE:
            return HttpResponseForbidden(
                "Esta página está disponible solo para cuentas de cliente."
            )
        return view_func(request, *args, **kwargs)

    return vista_protegida


def solo_personal(view_func):
    @wraps(view_func)
    @login_required
    def vista_protegida(request, *args, **kwargs):
        if request.user.rol not in (
            Usuario.Rol.ADMINISTRADOR,
            Usuario.Rol.TECNICO,
        ):
            return HttpResponseForbidden(
                "Esta página está disponible solo para el personal."
            )
        return view_func(request, *args, **kwargs)

    return vista_protegida
