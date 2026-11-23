from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.models import Empresa, Paquete


class Diagnostico(models.Model):
    class NivelRiesgo(models.TextChoices):
        ALTO = "ALTO", "Alto"
        MEDIO = "MEDIO", "Medio"
        BAJO = "BAJO", "Bajo"

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        verbose_name="empresa",
    )
    paquete_recomendado = models.ForeignKey(
        Paquete,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name="paquete recomendado",
    )
    fecha_diagnostico = models.DateTimeField(
        auto_now_add=True,
        verbose_name="fecha del diagnóstico",
    )
    tiene_antivirus = models.BooleanField(default=False, verbose_name="tiene antivirus")
    tiene_respaldo = models.BooleanField(default=False, verbose_name="tiene respaldo")
    tiene_contrasenas_2fa = models.BooleanField(
        default=False,
        verbose_name="usa contraseñas y verificación en dos pasos",
    )
    tiene_firewall = models.BooleanField(default=False, verbose_name="tiene cortafuegos")
    tiene_actualizaciones = models.BooleanField(
        default=False,
        verbose_name="mantiene los sistemas actualizados",
    )
    tiene_politica_escrita = models.BooleanField(
        default=False,
        verbose_name="tiene política escrita",
    )
    indice_proteccion = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(6)],
        verbose_name="índice de protección",
    )
    nivel_riesgo = models.CharField(
        max_length=5,
        choices=NivelRiesgo.choices,
        verbose_name="nivel de riesgo",
    )

    class Meta:
        verbose_name = "diagnóstico"
        verbose_name_plural = "diagnósticos"
        ordering = ["-fecha_diagnostico"]

    def __str__(self):
        return f"Diagnóstico de {self.empresa}"


class Reporte(models.Model):
    diagnostico = models.ForeignKey(
        Diagnostico,
        on_delete=models.CASCADE,
        verbose_name="diagnóstico",
    )
    fecha_generacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="fecha de generación",
    )
    ruta_archivo = models.CharField(max_length=200, verbose_name="ruta del archivo")
    resumen = models.CharField(max_length=500, verbose_name="resumen")

    class Meta:
        verbose_name = "reporte"
        verbose_name_plural = "reportes"
        ordering = ["-fecha_generacion"]

    def __str__(self):
        return f"Reporte del {self.diagnostico}"
