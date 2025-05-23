from django.db import models
from multiselectfield import MultiSelectField

# Definindo as choices como variável global
METHOD_CHOICES = {
    "OBD": {
        'allOBD': 'allOBD',
        'partOBD': 'partOBD'
    },
    "BENCH": {
        'allBENCH': 'allBENCH',
        'partBENCH': 'partBENCH'
    },
}

def get_flat_choices():
    """Transforma METHOD_CHOICES em lista de tuplas simples"""
    flat_choices = []
    for grupo in METHOD_CHOICES.values():
        flat_choices.extend(grupo.items())
    return flat_choices

class Veiculo(models.Model):
    FREQUENCIA_CHOICES = [
        ('315', '315 MHz'),
        ('433', '433 MHz'),
    ]

    # Campos principais
    pais = models.CharField(max_length=100, verbose_name='País')
    brand = models.CharField(max_length=100, verbose_name='Marca')
    modelo = models.CharField(max_length=100, verbose_name='Modelo')
    ano = models.CharField(max_length=20, verbose_name='Ano')

    # Campos opcionais
    sistema = models.CharField(max_length=100, blank=True, verbose_name='Sistema')
    tipo_chave = models.CharField(max_length=100, blank=True, verbose_name='Tipo de Chave')
    transponder = models.CharField(max_length=100, blank=True, verbose_name='Transponder')
    immo_part_replacement = models.CharField(max_length=100, blank=True, verbose_name='Substituição da Peça IMMO')

    # Campos com Choices simples
    frequencia = models.CharField(
        max_length=3,
        choices=[('', '---------')] + FREQUENCIA_CHOICES,
        blank=True,
        verbose_name='Frequência'
    )

    # Campos com MultiSelectField (choices do tipo METHOD_CHOICES)
    add_key = MultiSelectField(
        choices=get_flat_choices(),
        blank=True,
        verbose_name='Add Key'
    )
    read_password = MultiSelectField(
        choices=get_flat_choices(),
        blank=True,
        verbose_name='Read Password'
    )
    remote_learning = MultiSelectField(
        choices=get_flat_choices(),
        blank=True,
        verbose_name='Remote Learning'
    )
    key_lost = MultiSelectField(
        choices=get_flat_choices(),
        blank=True,
        verbose_name='Key Lost'
    )

    def __str__(self):
        return f"{self.brand} {self.modelo} ({self.ano})"
