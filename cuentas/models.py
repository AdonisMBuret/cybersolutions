from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models


class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El correo electrónico es obligatorio.")
        email = self.normalize_email(email)
        usuario = self.model(email=email, **extra_fields)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields["rol"] = Usuario.Rol.ADMINISTRADOR

        if extra_fields.get("is_staff") is not True:
            raise ValueError("El superusuario debe tener is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("El superusuario debe tener is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    class Rol(models.TextChoices):
        CLIENTE = "CLIENTE", "Cliente"
        ADMINISTRADOR = "ADMINISTRADOR", "Administrador"
        TECNICO = "TECNICO", "Técnico"

    class Estado(models.TextChoices):
        ACTIVO = "ACTIVO", "Activo"
        INACTIVO = "INACTIVO", "Inactivo"

    email = models.EmailField(unique=True, verbose_name="correo electrónico")
    rol = models.CharField(
        max_length=13,
        choices=Rol.choices,
        default=Rol.CLIENTE,
        verbose_name="rol",
    )
    estado = models.CharField(
        max_length=8,
        choices=Estado.choices,
        default=Estado.ACTIVO,
        verbose_name="estado",
    )
    is_staff = models.BooleanField(default=False, verbose_name="es personal")
    is_active = models.BooleanField(default=True, verbose_name="está activo")
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name="fecha de registro",
    )

    objects = UsuarioManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"
        ordering = ["email"]

    def __str__(self):
        return self.email
