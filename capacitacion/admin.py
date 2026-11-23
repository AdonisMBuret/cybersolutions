from django.contrib import admin

from .models import Leccion, ProgresoLeccion


@admin.register(Leccion)
class LeccionAdmin(admin.ModelAdmin):
    list_display = ("titulo", "tipo", "duracion_minutos", "orden", "estado")
    list_filter = ("tipo", "estado")
    search_fields = ("titulo",)
    ordering = ("orden",)


@admin.register(ProgresoLeccion)
class ProgresoLeccionAdmin(admin.ModelAdmin):
    list_display = ("usuario", "leccion", "estado", "puntaje", "fecha_completada")
    list_filter = ("estado",)
    search_fields = ("usuario__email", "leccion__titulo")
