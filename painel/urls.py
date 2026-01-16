from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='painel_home'),
    path('dashboard/', views.dashboard, name='painel_dashboard'),
    path('settings/', views.settings_view, name='painel_settings'),
    path('users/new/', views.user_create, name='painel_user_create'),
    path('logout/', views.sair, name='painel_logout'),
]
