from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from .forms import VeiculoForm
from .models import Veiculo
from django.db.models import Q
from django.core.paginator import Paginator
from .metrics import (
    VEICULOS_CADASTRADOS,
    VEICULOS_ATUALIZADOS,
    VEICULOS_ATUALIZACAO_ERRO,
    FILTROS_CONSULTADOS,
    AJAX_FILTRO
)
from .decorators import form_metrics

# views.py - Lógica de Negócio para o App 'form'

def cadastrar_veiculo(request):
    """
    Processa o formulário de cadastro de um novo veículo.
    
    Se a requisição for POST, valida e salva o formulário.
    Caso contrário, exibe um formulário vazio.
    """
    if request.method == 'POST':
        form = VeiculoForm(request.POST)
        if form.is_valid():
            # Salva o novo veículo no banco de dados
            form.save()
            VEICULOS_CADASTRADOS.inc()
            messages.success(request, 'Veículo cadastrado com sucesso!')
            # Redireciona para a página de listagem após o sucesso
            return redirect('index_form')
        else:
            # Exibe mensagem de erro se a validação falhar
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = VeiculoForm()
    
    # Renderiza o template de criação com o formulário (vazio ou com erros)
    return render(request, 'form/create.html', {'form': form})

def index(request):
    """
    Exibe a lista de veículos com suporte a filtros e paginação.
    """
    FILTROS_CONSULTADOS.inc()
    # Inicializa um objeto Q vazio para construir a consulta de filtros
    query_filters = Q()
    
    # Mapeamento dos parâmetros de filtro da URL para os campos do modelo
    filter_params = {
        'pais': 'pais__icontains',
        'brand': 'brand__icontains',
        'modelo': 'modelo__icontains',
        'ano': 'ano__icontains',
    }
    
    # Aplica os filtros dinamicamente
    for param, field_lookup in filter_params.items():
        value = request.GET.get(param)
        if value:
            # Adiciona a condição de filtro ao objeto Q
            query_filters &= Q(**{field_lookup: value})
    
    # Busca os veículos aplicando os filtros e ordenando por campos chave
    veiculos_filtrados = Veiculo.objects.filter(query_filters).order_by('pais', 'brand', 'modelo', 'ano')

    # --- Paginação ---
    # Define o paginador com 10 itens por página
    paginator = Paginator(object_list=veiculos_filtrados, per_page=10)
    # Obtém o número da página a partir dos parâmetros da requisição
    page_number = request.GET.get('page')
    # Obtém o objeto da página solicitada
    page_obj = paginator.get_page(page_number)
    
    # Renderiza o template de índice com os dados paginados e os filtros aplicados
    return render(request, 'form/index.html', {
        'page_obj': page_obj,
        # Passa os parâmetros GET para manter o estado dos filtros no template
        'filtros': request.GET,
    })



def get_opcoes_filtro(request):
    """
    Retorna opções de filtro (países, marcas, modelos, anos) em formato JSON,
    baseado nos filtros de país e marca já aplicados.
    
    Útil para preencher dinamicamente dropdowns de filtro.
    """
    AJAX_FILTRO.inc()
    # Obtém os parâmetros de filtro da requisição
    pais_filtro = request.GET.get('pais', '')
    marca_filtro = request.GET.get('marca', '')
    
    # Inicia a consulta com todos os veículos
    consulta_filtrada = Veiculo.objects.all()
    
    # Aplica filtro de país, se fornecido
    if pais_filtro:
        consulta_filtrada = consulta_filtrada.filter(pais__icontains=pais_filtro)
    # Aplica filtro de marca, se fornecido
    if marca_filtro:
        consulta_filtrada = consulta_filtrada.filter(brand__icontains=marca_filtro)
    
    # Prepara os dados de resposta, obtendo valores distintos e ordenados
    opcoes_filtro = {
        'paises': list(consulta_filtrada.order_by('pais').values_list('pais', flat=True).distinct()),
        'marcas': list(consulta_filtrada.order_by('brand').values_list('brand', flat=True).distinct()),
        'modelos': list(consulta_filtrada.order_by('modelo').values_list('modelo', flat=True).distinct()),
        'anos': list(consulta_filtrada.order_by('ano').values_list('ano', flat=True).distinct()),
    }
    
    # Retorna as opções de filtro como resposta JSON
    return JsonResponse(opcoes_filtro)

def update_vehicle(request):
    """
    Atualiza um campo específico de um veículo via requisição POST.
    
    Esta função é uma alternativa mais simples para update_vehicle_field,
    mas é menos robusta em termos de tratamento de exibição de valores.
    """
    if request.method == 'POST':
        try:
            # Obtém o ID, nome do campo e novo valor da requisição POST
            veiculo_id = request.POST.get('id')
            nome_campo = request.POST.get('field')
            novo_valor = request.POST.get('value')
            
            # Busca o veículo pelo ID
            veiculo = Veiculo.objects.get(id=veiculo_id)
            
            # Atualiza o atributo do objeto e salva no banco de dados
            setattr(veiculo, nome_campo, novo_valor)
            veiculo.save()
            VEICULOS_ATUALIZADOS.labels(nome_campo).inc()
            # Retorna sucesso com o novo valor
            return JsonResponse({
                'status': 'success',
                'new_display': novo_valor
            })
        except Veiculo.DoesNotExist:
            # Trata o caso de veículo não encontrado
            return JsonResponse({'status': 'error', 'message': 'Veículo não encontrado'}, status=404)
        except Exception as e:
            VEICULOS_ATUALIZACAO_ERRO.inc()
            # Trata outros erros de atualização
            return JsonResponse({'status': 'error', 'message': f'Erro ao atualizar veículo: {str(e)}'}, status=400)
            
    # Retorna erro se o método não for POST
    return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)

def update_vehicle_field(request):
    """
    Atualiza um campo específico de um veículo e retorna o valor de exibição (display value)
    para campos com choices definidos no modelo.
    
    É a função de atualização mais robusta.
    """
    if request.method == 'POST':
        # Obtém os dados da requisição POST
        veiculo_id = request.POST.get('id')
        nome_campo = request.POST.get('field')
        novo_valor = request.POST.get('value')
        
        try:
            # 1. Busca o veículo
            veiculo = Veiculo.objects.get(id=veiculo_id)
            
            # 2. Atualiza o campo e salva, especificando o campo para otimização
            setattr(veiculo, nome_campo, novo_valor)
            veiculo.save(update_fields=[nome_campo])

            # 3. Prepara os dados de resposta
            # Tenta obter o valor de exibição (display value) se o campo tiver choices
            display_func = getattr(veiculo, f'get_{nome_campo}_display', lambda: novo_valor)
            display_value = display_func()

            VEICULOS_ATUALIZADOS.labels(nome_campo).inc()

            response_data = {
                'status': 'success',
                'new_value': novo_valor,
                'display_value': display_value
            }

            # 4. Retorna a resposta JSON
            return JsonResponse(response_data)
        
        except Veiculo.DoesNotExist:
            # Trata o caso de veículo não encontrado
            return JsonResponse({'status': 'error', 'message': 'Veículo não encontrado'}, status=404)
        except Exception as e:
            VEICULOS_ATUALIZACAO_ERRO.inc()
            # Trata outros erros de atualização
            return JsonResponse({'status': 'error', 'message': f'Erro ao atualizar campo: {str(e)}'}, status=400)
        
    # Retorna erro se o método não for POST
    return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)