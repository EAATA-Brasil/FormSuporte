from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.index, name='index_ocorrencia'),
    path("filter_data/", views.filter_data_view, name="filter_data"),
    path('login/', views.login_view, name="login_ocorrencias"),
    path('logout/', views.logout_view, name='logout'),
    path('cadastrar_ocorrencia/', views.subir_ocorrencia, name="subir_ocorrencia"),
    path('update_ocorrencia/', views.alterar_dados, name="update_ocorrencia/"),
    path('criar_usuario/', views.criar_usuario, name="criar_usuario"),
]
