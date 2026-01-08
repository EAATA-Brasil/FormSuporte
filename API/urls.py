# urls.py - Definições de Rotas (URLs) para o App 'API'

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Cria um roteador para as ViewSets do Django REST Framework
router = DefaultRouter()
# Rota para listar e recuperar equipamentos
router.register(r'equipamentos', views.EquipamentosViewSet)
# Rota para listar e recuperar tipos de equipamento
router.register(r'tiposEquipamento', views.TipoEquipamentoViewSet)
# Rota para listar e recuperar marcas de equipamento
router.register(r'marcasEquipamento', views.MarcaEquipamentoViewSet)
# Rota para listar e recuperar clientes (serial, nome, cnpj, tel, equipamento)
router.register(r'clientes', views.ClienteViewSet)

# Definição dos padrões de URL
urlpatterns = [
    # Inclui as rotas geradas pelo roteador (para as ViewSets)
    path('', include(router.urls)),
    
    # Rota específica para a geração de PDF (usando @api_view)
    path('generate-pdf/', views.generate_pdf, name='generate_pdf'),
]