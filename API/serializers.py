# serializers.py
from rest_framework import serializers
from .models import Equipamentos, TipoEquipamento, MarcaEquipamento

class TipoEquipamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoEquipamento
        fields = '__all__'

class MarcaEquipamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarcaEquipamento
        fields = '__all__'

class EquipamentosSerializer(serializers.ModelSerializer):
    tipo = TipoEquipamentoSerializer(read_only=True)

    class Meta:
        model = Equipamentos
        fields = '__all__'
