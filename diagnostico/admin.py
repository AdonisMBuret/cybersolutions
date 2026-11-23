from django.contrib import admin

from .models import Diagnostico, Reporte


@admin.register(Diagnostico)
class DiagnosticoAdmin(admin.ModelAdmin):
    list_display = ("empresa", "nivel_riesgo", "indice_proteccion", "fecha_diagnostico")
    list_filter = ("nivel_riesgo", "fecha_diagnostico")
    search_fields = ("empresa__nombre_comercial",)


@admin.register(Reporte)
class ReporteAdmin(admin.ModelAdmin):
    list_display = ("diagnostico", "fecha_generacion", "ruta_archivo")
    list_filter = ("fecha_generacion",)
    search_fields = ("resumen", "ruta_archivo", "diagnostico__empresa__nombre_comercial")
