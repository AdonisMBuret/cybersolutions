from django import forms


class DiagnosticoForm(forms.Form):
    RESPUESTA_SI = "si"

    tiene_antivirus = forms.ChoiceField(
        label="¿Tus equipos tienen un antivirus instalado y actualizado?",
        choices=(("si", "Sí"), ("no", "No")),
        widget=forms.RadioSelect(attrs={"class": "btn-check"}),
    )
    tiene_respaldo = forms.ChoiceField(
        label="¿Haces copias de respaldo de la información de tu empresa?",
        choices=(("si", "Sí"), ("no", "No")),
        widget=forms.RadioSelect(attrs={"class": "btn-check"}),
    )
    tiene_contrasenas_2fa = forms.ChoiceField(
        label="¿Usas contraseñas seguras y doble autenticación?",
        choices=(("si", "Sí"), ("no", "No")),
        widget=forms.RadioSelect(attrs={"class": "btn-check"}),
    )
    tiene_firewall = forms.ChoiceField(
        label="¿Tienes un firewall o protección para la red?",
        choices=(("si", "Sí"), ("no", "No")),
        widget=forms.RadioSelect(attrs={"class": "btn-check"}),
    )
    tiene_actualizaciones = forms.ChoiceField(
        label="¿Actualizas tus equipos y programas periódicamente?",
        choices=(("si", "Sí"), ("no", "No")),
        widget=forms.RadioSelect(attrs={"class": "btn-check"}),
    )
    tiene_politica_escrita = forms.ChoiceField(
        label="¿Tu empresa tiene una política de seguridad por escrito?",
        choices=(("si", "Sí"), ("no", "No")),
        widget=forms.RadioSelect(attrs={"class": "btn-check"}),
    )
