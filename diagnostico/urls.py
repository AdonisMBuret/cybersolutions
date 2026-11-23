from django.urls import path

from . import views

app_name = "diagnostico"
urlpatterns = [
    path("", views.cuestionario, name="cuestionario"),
    path("resultado/<int:id>/", views.resultado, name="resultado"),
    path("<int:id>/reporte.pdf", views.reporte_pdf, name="reporte_pdf"),
]
