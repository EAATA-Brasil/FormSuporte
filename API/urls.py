from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EquipamentosViewSet, TipoEquipamentoViewSet, MarcaEquipamentoViewSet

router = DefaultRouter()
router.register(r'equipamentos', EquipamentosViewSet, basename='equipamentos')
router.register(r'tipoEquipamento', TipoEquipamentoViewSet, basename='tipoEquipamento')
router.register(r'marcaEquipamento', MarcaEquipamentoViewSet, basename='marcaEquipamento')

urlpatterns = [
    path('', include(router.urls)),
]
