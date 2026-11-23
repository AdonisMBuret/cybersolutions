from django.conf import settings
from django.db import models


class Empresa(models.Model):
    class Sector(models.TextChoices):
        COMERCIO = "Comercio", "Comercio"
        SERVICIOS_PROFESIONALES = "Servicios profesionales", "Servicios profesionales"
        SALUD = "Salud", "Salud"
        EDUCACION = "Educación", "Educación"
        RESTAURANTES = "Restaurantes", "Restaurantes"
        MANUFACTURA = "Manufactura", "Manufactura"
        TECNOLOGIA = "Tecnología", "Tecnología"
        OTRO = "Otro", "Otro"

    class Tamano(models.TextChoices):
        MICRO = "MICRO", "Micro"
        PEQUENA = "PEQUENA", "Pequeña"

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="usuario",
    )
    nombre_comercial = models.CharField(
        max_length=80,
        verbose_name="nombre comercial",
    )
    rnc = models.CharField(max_length=11, blank=True, verbose_name="RNC")
    sector = models.CharField(
        max_length=25,
        choices=Sector.choices,
        verbose_name="sector",
    )
    tamano = models.CharField(
        max_length=7,
        choices=Tamano.choices,
        verbose_name="tamaño",
    )
    cantidad_empleados = models.IntegerField(verbose_name="cantidad de empleados")
    cantidad_equipos = models.IntegerField(verbose_name="cantidad de equipos")
    telefono = models.CharField(max_length=13, verbose_name="teléfono")
    direccion = models.CharField(max_length=100, verbose_name="dirección")
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name="fecha de registro",
    )

    class Meta:
        verbose_name = "empresa"
        verbose_name_plural = "empresas"
        ordering = ["nombre_comercial"]

    def __str__(self):
        return self.nombre_comercial


class Paquete(models.Model):
    class Nombre(models.TextChoices):
        BASICO = "Básico", "Básico"
        INTERMEDIO = "Intermedio", "Intermedio"
        COMPLETO = "Completo", "Completo"

    class Estado(models.TextChoices):
        ACTIVO = "ACTIVO", "Activo"
        INACTIVO = "INACTIVO", "Inactivo"

    nombre = models.CharField(
        max_length=20,
        choices=Nombre.choices,
        unique=True,
        verbose_name="nombre",
    )
    descripcion = models.CharField(max_length=200, verbose_name="descripción")
    servicios_incluidos = models.CharField(
        max_length=300,
        verbose_name="servicios incluidos",
    )
    precio_mensual = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="precio mensual",
    )
    estado = models.CharField(
        max_length=8,
        choices=Estado.choices,
        verbose_name="estado",
    )

    class Meta:
        verbose_name = "paquete"
        verbose_name_plural = "paquetes"
        ordering = ["precio_mensual"]

    def __str__(self):
        return self.nombre


class Contrato(models.Model):
    class TipoContrato(models.TextChoices):
        MENSUAL = "MENSUAL", "Mensual"
        TRIMESTRAL = "TRIMESTRAL", "Trimestral"
        ANUAL = "ANUAL", "Anual"

    class Estado(models.TextChoices):
        SOLICITADO = "SOLICITADO", "Solicitado"
        ACTIVO = "ACTIVO", "Activo"
        VENCIDO = "VENCIDO", "Vencido"
        CANCELADO = "CANCELADO", "Cancelado"

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        verbose_name="empresa",
    )
    paquete = models.ForeignKey(
        Paquete,
        on_delete=models.PROTECT,
        verbose_name="paquete",
    )
    tipo_contrato = models.CharField(
        max_length=10,
        choices=TipoContrato.choices,
        verbose_name="tipo de contrato",
    )
    precio_acordado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="precio acordado",
    )
    fecha_solicitud = models.DateTimeField(
        auto_now_add=True,
        verbose_name="fecha de solicitud",
    )
    fecha_inicio = models.DateField(
        blank=True,
        null=True,
        verbose_name="fecha de inicio",
    )
    fecha_fin = models.DateField(
        blank=True,
        null=True,
        verbose_name="fecha de finalización",
    )
    estado = models.CharField(
        max_length=10,
        choices=Estado.choices,
        default=Estado.SOLICITADO,
        verbose_name="estado",
    )

    class Meta:
        verbose_name = "contrato"
        verbose_name_plural = "contratos"
        ordering = ["-fecha_solicitud"]

    def __str__(self):
        return f"{self.empresa} - {self.paquete}"


class Pago(models.Model):
    class MetodoPago(models.TextChoices):
        TARJETA = "TARJETA", "Tarjeta"
        TRANSFERENCIA = "TRANSFERENCIA", "Transferencia"

    class Estado(models.TextChoices):
        PAGADO = "PAGADO", "Pagado"
        PENDIENTE = "PENDIENTE", "Pendiente"
        RECHAZADO = "RECHAZADO", "Rechazado"

    contrato = models.ForeignKey(
        Contrato,
        on_delete=models.CASCADE,
        verbose_name="contrato",
    )
    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="monto",
    )
    fecha_pago = models.DateTimeField(auto_now_add=True, verbose_name="fecha de pago")
    metodo_pago = models.CharField(
        max_length=13,
        choices=MetodoPago.choices,
        verbose_name="método de pago",
    )
    referencia = models.CharField(max_length=30, verbose_name="referencia")
    estado = models.CharField(
        max_length=9,
        choices=Estado.choices,
        verbose_name="estado",
    )

    class Meta:
        verbose_name = "pago"
        verbose_name_plural = "pagos"
        ordering = ["-fecha_pago"]

    def __str__(self):
        return f"Pago {self.monto} - {self.contrato}"
