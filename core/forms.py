from django import forms

from .models import Contrato, Paquete, Pago


class SolicitudContratoForm(forms.Form):
    paquete = forms.ModelChoiceField(
        queryset=Paquete.objects.none(),
        widget=forms.HiddenInput,
        error_messages={
            "required": "Selecciona un paquete.",
            "invalid_choice": "El paquete seleccionado no está disponible.",
        },
    )
    tipo_contrato = forms.ChoiceField(
        label="Tipo de contrato",
        choices=(
            (Contrato.TipoContrato.MENSUAL, "Mensual (sin descuento)"),
            (Contrato.TipoContrato.TRIMESTRAL, "Trimestral (5 % de descuento)"),
            (Contrato.TipoContrato.ANUAL, "Anual (10 % de descuento)"),
        ),
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "id": "tipo-contrato",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["paquete"].queryset = Paquete.objects.filter(
            estado=Paquete.Estado.ACTIVO
        )


class PagoSimuladoForm(forms.Form):
    nombre_titular = forms.CharField(
        label="Nombre del titular",
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "autocomplete": "cc-name",
            }
        ),
    )
    metodo_pago = forms.ChoiceField(
        label="Método de pago",
        choices=Pago.MetodoPago.choices,
        widget=forms.Select(attrs={"class": "form-select"}),
    )


class FiltroPanelAdminForm(forms.Form):
    q = forms.CharField(
        label="Buscar empresa",
        required=False,
        max_length=80,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Nombre de empresa",
            }
        ),
    )
    estado = forms.ChoiceField(
        label="Estado del contrato",
        required=False,
        choices=[("", "Todos los estados"), *Contrato.Estado.choices],
        widget=forms.Select(attrs={"class": "form-select"}),
    )
