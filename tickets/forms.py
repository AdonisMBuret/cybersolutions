from django import forms

from .models import SeguimientoTicket, Ticket


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ("asunto", "tipo", "prioridad", "descripcion")
        labels = {
            "asunto": "Asunto",
            "tipo": "Tipo",
            "prioridad": "Prioridad",
            "descripcion": "Descripción",
        }
        widgets = {
            "asunto": forms.TextInput(attrs={"class": "form-control"}),
            "tipo": forms.Select(attrs={"class": "form-select"}),
            "prioridad": forms.Select(attrs={"class": "form-select"}),
            "descripcion": forms.Textarea(
                attrs={"class": "form-control", "rows": 5}
            ),
        }


class SeguimientoTicketForm(forms.ModelForm):
    class Meta:
        model = SeguimientoTicket
        fields = ("mensaje",)
        labels = {"mensaje": "Mensaje"}
        widgets = {
            "mensaje": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Escriba un mensaje...",
                }
            )
        }


class CambioEstadoTicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ("estado",)
        labels = {"estado": "Estado"}
        widgets = {"estado": forms.Select(attrs={"class": "form-select"})}


class FiltroTicketForm(forms.Form):
    estado = forms.ChoiceField(
        label="Filtrar por estado",
        required=False,
        choices=[("", "Todos los estados"), *Ticket.Estado.choices],
        widget=forms.Select(attrs={"class": "form-select"}),
    )
