from django.urls import path

from . import views

app_name = "tickets"
urlpatterns = [
    path("", views.lista_tickets, name="lista"),
    path("nuevo/", views.nuevo_ticket, name="nuevo"),
    path("gestion/", views.gestion_tickets, name="gestion"),
    path("<int:id>/", views.detalle_ticket, name="detalle"),
]
