"""
URL configuration for Form_Suporte project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    # URL para a interface de administração do Django
    path("admin/", admin.site.urls),

    # Inclui as URLs da aplicação 'form' para formulários de suporte
    path("form/", include("form.urls")),

    # Inclui as URLs da aplicação 'situacao_veiculo' para gerenciamento de veículos
    path("situacao/", include("situacao_veiculo.urls")),

    # Inclui as URLs da aplicação 'ocorrencia_erro' para registro de ocorrências
    path("ocorrencia/", include("ocorrencia_erro.urls")),

    # Inclui as URLs da aplicação 'API' para endpoints REST
    path("api/", include("API.urls")),

    # Inclui as URLs da aplicação 'simulador' para funcionalidades de simulação
    path("simulador/", include("simulador.urls")),
]
