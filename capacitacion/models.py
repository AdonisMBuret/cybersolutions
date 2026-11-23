from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Leccion(models.Model):
    class Tipo(models.TextChoices):
        LECCION = "LECCION", "Lección"
        SIMULACRO = "SIMULACRO", "Simulacro"

    class Estado(models.TextChoices):
        ACTIVA = "ACTIVA", "Activa"
        INACTIVA = "INACTIVA", "Inactiva"

    titulo = models.CharField(max_length=80, verbose_name="título")
    contenido = models.TextField(verbose_name="contenido")
    duracion_minutos = models.IntegerField(verbose_name="duración en minutos")
    orden = models.IntegerField(verbose_name="orden")
    tipo = models.CharField(max_length=9, choices=Tipo.choices, verbose_name="tipo")
    estado = models.CharField(
        max_length=8,
        choices=Estado.choices,
        verbose_name="estado",
    )

    class Meta:
        verbose_name = "lección"
        verbose_name_plural = "lecciones"
        ordering = ["orden", "titulo"]

    def __str__(self):
        return self.titulo


class ProgresoLeccion(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        EN_CURSO = "EN_CURSO", "En curso"
        COMPLETADA = "COMPLETADA", "Completada"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="usuario",
    )
    leccion = models.ForeignKey(
        Leccion,
        on_delete=models.CASCADE,
        verbose_name="lección",
    )
    estado = models.CharField(
        max_length=10,
        choices=Estado.choices,
        verbose_name="estado",
    )
    puntaje = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="puntaje",
    )
    fecha_completada = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="fecha de finalización",
    )

    class Meta:
        verbose_name = "progreso de lección"
        verbose_name_plural = "progresos de lecciones"
        ordering = ["usuario__email", "leccion__orden"]
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "leccion"],
                name="progreso_usuario_leccion_unico",
            )
        ]

    def __str__(self):
        return f"{self.usuario} - {self.leccion}"
