from rest_framework import viewsets
from .models import Equipamentos, TipoEquipamento, MarcaEquipamento
from .serializers import EquipamentosSerializer, TipoEquipamentoSerializer, MarcaEquipamentoSerializer

class EquipamentosViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Equipamentos.objects.all().order_by('nome')
    serializer_class = EquipamentosSerializer

class TipoEquipamentoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TipoEquipamento.objects.all().order_by('nome')
    serializer_class = TipoEquipamentoSerializer

class MarcaEquipamentoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MarcaEquipamento.objects.all().order_by('nome')
    serializer_class = MarcaEquipamentoSerializer
