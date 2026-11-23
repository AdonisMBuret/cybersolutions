from django.contrib import admin

from .models import Contrato, Empresa, Pago, Paquete


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ("nombre_comercial", "usuario", "sector", "tamano", "fecha_registro")
    list_filter = ("sector", "tamano")
    search_fields = ("nombre_comercial", "rnc", "usuario__email")


@admin.register(Paquete)
class PaqueteAdmin(admin.ModelAdmin):
    list_display = ("nombre", "precio_mensual", "estado")
    list_filter = ("estado",)
    search_fields = ("nombre",)


@admin.register(Contrato)
class ContratoAdmin(admin.ModelAdmin):
    list_display = ("empresa", "paquete", "tipo_contrato", "estado", "fecha_solicitud")
    list_filter = ("tipo_contrato", "estado")
    search_fields = ("empresa__nombre_comercial", "paquete__nombre")


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ("contrato", "monto", "metodo_pago", "estado", "fecha_pago")
    list_filter = ("metodo_pago", "estado")
    search_fields = ("referencia", "contrato__empresa__nombre_comercial")
