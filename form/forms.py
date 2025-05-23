from django import forms
from .models import Veiculo, METHOD_CHOICES

def get_flat_choices():
    """Reutiliza a mesma função do models.py"""
    flat_choices = []
    for grupo in METHOD_CHOICES.values():
        flat_choices.extend(grupo.items())
    return flat_choices

class VeiculoForm(forms.ModelForm):
    # Usando MultipleChoiceField com CheckboxSelectMultiple para múltiplos checkboxes
    add_key = forms.MultipleChoiceField(
        choices=get_flat_choices(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'method-checkbox'})
    )

    read_password = forms.MultipleChoiceField(
        choices=get_flat_choices(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'method-checkbox'})
    )

    remote_learning = forms.MultipleChoiceField(
        choices=get_flat_choices(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'method-checkbox'})
    )
    keys_lost = forms.MultipleChoiceField(
        choices=get_flat_choices(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'method-checkbox'})
    )

    # A Meta da classe se mantém, apenas ajustando os widgets
    class Meta:
        model = Veiculo
        fields = '__all__'
        widgets = {
            'frequencia': forms.Select(attrs={'class': 'form-select frequency-select'}),
            'tipo_chave': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: ID46, Crypto'}),
            'transponder': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: T5, Megamos'}),
            'immo_part_replacement': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: NEC, EEPROM'})
        }
        labels = {
            'add_key': 'Adicionar Chave (OBD)',
            'read_password': 'Ler Senha (Bench)',
            'remote_learning': 'Aprendizado Remoto',
            'keys_lost': 'All Keys Lost'
        }

