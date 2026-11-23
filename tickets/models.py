from django.conf import settings
from django.db import models

from core.models import Empresa


class Ticket(models.Model):
    class Tipo(models.TextChoices):
        INCIDENTE = "INCIDENTE", "Incidente"
        CONSULTA = "CONSULTA", "Consulta"
        SOLICITUD = "SOLICITUD", "Solicitud"

    class Prioridad(models.TextChoices):
        BAJA = "BAJA", "Baja"
        MEDIA = "MEDIA", "Media"
        ALTA = "ALTA", "Alta"

    class Estado(models.TextChoices):
        ABIERTO = "ABIERTO", "Abierto"
        EN_PROCESO = "EN_PROCESO", "En proceso"
        CERRADO = "CERRADO", "Cerrado"

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        verbose_name="empresa",
    )
    asunto = models.CharField(max_length=80, verbose_name="asunto")
    descripcion = models.CharField(max_length=500, verbose_name="descripción")
    tipo = models.CharField(max_length=9, choices=Tipo.choices, verbose_name="tipo")
    prioridad = models.CharField(
        max_length=5,
        choices=Prioridad.choices,
        verbose_name="prioridad",
    )
    estado = models.CharField(
        max_length=10,
        choices=Estado.choices,
        default=Estado.ABIERTO,
        verbose_name="estado",
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="fecha de creación",
    )
    fecha_cierre = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="fecha de cierre",
    )

    class Meta:
        verbose_name = "ticket"
        verbose_name_plural = "tickets"
        ordering = ["-fecha_creacion"]

    def __str__(self):
        return self.asunto


class SeguimientoTicket(models.Model):
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        verbose_name="ticket",
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="usuario",
    )
    mensaje = models.CharField(max_length=500, verbose_name="mensaje")
    fecha_seguimiento = models.DateTimeField(
        auto_now_add=True,
        verbose_name="fecha de seguimiento",
    )

    class Meta:
        verbose_name = "seguimiento de ticket"
        verbose_name_plural = "seguimientos de tickets"
        ordering = ["fecha_seguimiento"]

    def __str__(self):
        return f"Seguimiento de {self.ticket}"
