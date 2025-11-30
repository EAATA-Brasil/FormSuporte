# serializers.py - Definições de Serializers para o App 'API'

from rest_framework import serializers
from .models import Equipamentos, TipoEquipamento, MarcaEquipamento

class TipoEquipamentoSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo TipoEquipamento.
    Serializa todos os campos.
    """
    class Meta:
        model = TipoEquipamento
        fields = '__all__'

class MarcaEquipamentoSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo MarcaEquipamento.
    Serializa todos os campos.
    """
    class Meta:
        model = MarcaEquipamento
        fields = '__all__'

class EquipamentosSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Equipamentos.
    Inclui o tipo de equipamento serializado (somente leitura).
    """
    # Campo aninhado para exibir os detalhes do TipoEquipamento
    tipo = TipoEquipamentoSerializer(read_only=True)

    class Meta:
        model = Equipamentos
        # Serializa todos os campos do modelo Equipamentos, incluindo o campo 'tipo' aninhado
        fields = '__all__'
