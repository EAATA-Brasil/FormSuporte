from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('buscar/', views.buscar_serial, name='buscar_serial'),
    path('cadastrar/', views.cadastrar_serial, name='cadastrar_serial'),
    path('api/cliente/update', views.api_atualizar_cliente, name='api_atualizar_cliente'),

    # ==== API usada pelo popup de atualização ====
    path('api/cliente', views.api_buscar_cliente, name='api_buscar_cliente'),
]
