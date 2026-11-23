from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.password_validation import validate_password

from .models import Usuario


class UsuarioCreacionForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput,
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput,
    )

    class Meta:
        model = Usuario
        fields = ("email", "rol", "estado", "is_staff", "is_active")

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        if password2:
            validate_password(password2, self.instance)
        return password2

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.set_password(self.cleaned_data["password1"])
        if commit:
            usuario.save()
            self.save_m2m()
        return usuario


class UsuarioCambioForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(label="Contraseña")

    class Meta:
        model = Usuario
        fields = "__all__"


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    add_form = UsuarioCreacionForm
    form = UsuarioCambioForm
    ordering = ("email",)
    list_display = ("email", "rol", "estado", "is_staff", "is_active")
    list_filter = ("rol", "estado", "is_staff", "is_active")
    search_fields = ("email",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Acceso", {"fields": ("rol", "estado", "is_staff", "is_active")}),
        ("Permisos", {"fields": ("is_superuser", "groups", "user_permissions")}),
        ("Fechas", {"fields": ("last_login", "fecha_registro")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "rol",
                    "estado",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )
    readonly_fields = ("last_login", "fecha_registro")
    filter_horizontal = ("groups", "user_permissions")
