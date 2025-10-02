from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Cria um roteador para as ViewSets da API RESTful.
# O DefaultRouter automaticamente gera as URLs para as operações CRUD (neste caso, ReadOnly).
router = DefaultRouter()
router.register(r\'equipamentos\', views.EquipamentosViewSet, basename=\'equipamentos\')
router.register(r\'tiposEquipamento\', views.TipoEquipamentoViewSet, basename=\'tiposEquipamento\')
router.register(r\'marcasEquipamento\', views.MarcaEquipamentoViewSet, basename=\'marcasEquipamento\')

# Define os padrões de URL para a aplicação API.
urlpatterns = [
    # Inclui as URLs geradas pelo roteador para as ViewSets.
    path(\'\', include(router.urls)),

    # URL para o endpoint de geração de PDF.
    # Lida com requisições POST para gerar um PDF de simulação de venda.
    path(\'generate-pdf/\', views.generate_pdf, name=\'generate_pdf\'),
]

