from django import forms


class SimulacroForm(forms.Form):
    RESPUESTA_SI = "si"

    def __init__(self, correos, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for correo in correos:
            self.fields[f"correo_{correo['id']}"] = forms.ChoiceField(
                label="¿Es fraude?",
                choices=(("si", "Sí"), ("no", "No")),
                widget=forms.RadioSelect(attrs={"class": "btn-check"}),
            )
