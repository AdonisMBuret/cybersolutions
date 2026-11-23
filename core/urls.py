from django.urls import path

from . import views

app_name = "core"
urlpatterns = [
    path("panel/", views.panel_cliente, name="panel"),
    path("panel-admin/", views.panel_administrador, name="panel_admin"),
    path("", views.inicio, name="inicio"),
    path("paquetes/", views.paquetes, name="paquetes"),
    path("pago/<int:id>/", views.pago, name="pago"),
]
