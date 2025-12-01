from django import forms
from .models import SerialVCI

class SerialVCIForm(forms.ModelForm):
    class Meta:
        model = SerialVCI
        fields = [
            "numero_vci",
            "numero_tablet",
            "numero_prog",
            "cliente",
            "email",
            "telefone",
            "pedido",
        ]
