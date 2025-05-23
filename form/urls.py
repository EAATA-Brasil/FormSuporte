from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('cadastrar/', views.cadastrar_veiculo, name='cadastrar_veiculo'),
    path('get-opcoes/', views.get_opcoes_filtro, name='get_opcoes_filtro'),
     path('update-vehicle/', views.update_vehicle, name='update_vehicle'),
     path('update-field/', views.update_vehicle_field, name='update_field'),
]