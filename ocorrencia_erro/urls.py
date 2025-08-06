from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('subir_ocorrencia/', views.subir_ocorrencia, name='subir_ocorrencia'),
    path('filter_data/', views.filter_data_view, name='filter_data'),
    path('update_ocorrencia/', views.update_record_view, name='update_ocorrencia/'),
    path('criar_usuario/', views.criar_usuario, name='criar_usuario'),
    path('login/', views.login_view, name='login_ocorrencias'),  
    path('logout/', views.logout_view, name='logout'),
    path('download_arquivo/<int:arquivo_id>/', views.download_arquivo, name='download_arquivo/'),
]

