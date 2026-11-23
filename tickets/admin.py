from django.contrib import admin

from .models import SeguimientoTicket, Ticket


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("asunto", "empresa", "tipo", "prioridad", "estado", "fecha_creacion")
    list_filter = ("tipo", "prioridad", "estado")
    search_fields = ("asunto", "empresa__nombre_comercial")


@admin.register(SeguimientoTicket)
class SeguimientoTicketAdmin(admin.ModelAdmin):
    list_display = ("ticket", "usuario", "fecha_seguimiento")
    list_filter = ("fecha_seguimiento",)
    search_fields = ("ticket__asunto", "usuario__email", "mensaje")
