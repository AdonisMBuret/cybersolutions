from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from core.models import Empresa
from .models import Usuario


class AccesoForm(forms.Form):
    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "autocomplete": "email",
                "autofocus": True,
            }
        ),
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "autocomplete": "current-password",
            }
        ),
    )


class RegistroForm(forms.Form):
    nombre_comercial = forms.CharField(
        label="Nombre comercial",
        max_length=80,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    sector = forms.ChoiceField(
        label="Sector",
        choices=Empresa.Sector.choices,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    tamano = forms.ChoiceField(
        label="Tamaño de la empresa",
        choices=(
            (Empresa.Tamano.MICRO, "Micro (1 a 15 trabajadores)"),
            (Empresa.Tamano.PEQUENA, "Pequeña (16 a 60 trabajadores)"),
        ),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    cantidad_empleados = forms.IntegerField(
        label="Cantidad de empleados",
        min_value=1,
        max_value=60,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    cantidad_equipos = forms.IntegerField(
        label="Cantidad de equipos",
        min_value=0,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    telefono = forms.CharField(
        label="Teléfono",
        max_length=13,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "autocomplete": "tel",
            }
        ),
    )
    direccion = forms.CharField(
        label="Dirección",
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "autocomplete": "email",
            }
        ),
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "autocomplete": "new-password",
            }
        ),
    )
    confirmar_password = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "autocomplete": "new-password",
            }
        ),
    )

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        if Usuario.objects.filter(email__iexact=email).exists():
            raise ValidationError(
                "Ya existe una cuenta registrada con este correo electrónico."
            )
        return email

    def clean(self):
        cleaned_data = super().clean()
        tamano = cleaned_data.get("tamano")
        cantidad_empleados = cleaned_data.get("cantidad_empleados")

        if tamano and cantidad_empleados is not None:
            if (
                tamano == Empresa.Tamano.MICRO
                and not 1 <= cantidad_empleados <= 15
            ):
                self.add_error(
                    "cantidad_empleados",
                    "Una microempresa debe tener entre 1 y 15 trabajadores.",
                )
            elif (
                tamano == Empresa.Tamano.PEQUENA
                and not 16 <= cantidad_empleados <= 60
            ):
                self.add_error(
                    "cantidad_empleados",
                    "Una pequeña empresa debe tener entre 16 y 60 trabajadores.",
                )

        password = cleaned_data.get("password")
        confirmar_password = cleaned_data.get("confirmar_password")
        email = cleaned_data.get("email")

        if password and confirmar_password:
            if password != confirmar_password:
                self.add_error(
                    "confirmar_password",
                    "Las contraseñas no coinciden.",
                )
            elif email:
                usuario = Usuario(email=email)
                try:
                    validate_password(password, user=usuario)
                except ValidationError as error:
                    self.add_error("password", error)

        return cleaned_data
