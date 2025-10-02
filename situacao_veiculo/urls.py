from django.urls import path
from . import views

# Define os padrões de URL para a aplicação 'situacao_veiculo'.
# Cada padrão mapeia uma URL para uma função de view específica.
urlpatterns = [
    # URL para a página inicial da aplicação 'situacao_veiculo'.
    # Exibe a interface para buscar o status de suporte de um veículo.
    path(\'\', views.index, name=\'index\'),

    # URL para processar a busca por um número de série.
    # Lida com a submissão do formulário de busca e exibe os resultados.
    path(\'buscar/\', views.buscar_serial, name=\'buscar_serial\'),
]

