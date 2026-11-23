"""Rutas principales del sitio."""
from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("", include("core.urls")),
    path("cuentas/", include("cuentas.urls")),
    path("diagnostico/", include("diagnostico.urls")),
    path("capacitacion/", include("capacitacion.urls")),
    path("tickets/", include("tickets.urls")),
    path("admin/", admin.site.urls),
]
