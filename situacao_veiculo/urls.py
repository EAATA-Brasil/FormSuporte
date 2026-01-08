from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('buscar/', views.buscar_serial, name='buscar_serial'),
    path('cadastrar/', views.cadastrar_serial, name='cadastrar_serial'),
    path('importar-excel/', views.importar_excel, name='importar_excel'),
    path('api/cliente/update', views.api_atualizar_cliente, name='api_atualizar_cliente'),

    # ==== API usada pelo popup de atualização ====
    # Nota: rota antiga removida para evitar acesso sem autenticação.
    # A busca por serial agora deve usar o endpoint protegido em /api/clientes/search/
]
