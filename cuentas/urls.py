from django.urls import path

from . import views

app_name = "cuentas"
urlpatterns = [
    path("acceso/", views.acceso, name="acceso"),
    path("registro/", views.registro, name="registro"),
    path("salir/", views.salir, name="salir"),
]
