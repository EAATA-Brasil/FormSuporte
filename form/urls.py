from django.urls import path
from . import views

# Define os padrões de URL para a aplicação 'form'.
# Cada padrão mapeia uma URL para uma função de view específica.
urlpatterns = [
    # URL para a página inicial da aplicação 'form'.
    # Exibe a lista de veículos e o formulário de busca/filtro.
    path(\'\', views.index, name=\'index_form\'),

    # URL para cadastrar um novo veículo.
    # Lida com a submissão do formulário de cadastro de veículos.
    path(\'cadastrar/\', views.cadastrar_veiculo, name=\'cadastrar_veiculo\'),

    # URL para obter opções de filtro dinâmicas (e.g., marcas, modelos).
    # Usado por requisições AJAX para popular campos de filtro no frontend.
    path(\'get-opcoes/\', views.get_opcoes_filtro, name=\'get_opcoes_filtro\'),

    # URL para atualizar os dados completos de um veículo.
    # Lida com a submissão do formulário de edição de veículo.
    path(\'update-vehicle/\', views.update_vehicle, name=\'update_vehicle\'),

    # URL para atualizar um campo específico de um veículo.
    # Usado para atualizações parciais ou rápidas de dados de veículo.
    path(\'update-field/\', views.update_vehicle_field, name=\'update_field\'),
]

