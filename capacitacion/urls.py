from django.urls import path

from . import views

app_name = "capacitacion"
urlpatterns = [
    path("", views.lista_lecciones, name="lista"),
    path("leccion/<int:id>/", views.leccion, name="leccion"),
    path("simulacro/<int:id>/", views.simulacro, name="simulacro"),
]
