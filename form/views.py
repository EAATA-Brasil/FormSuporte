from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from .forms import VeiculoForm
from .models import Veiculo
from django.db.models import Q
from django.core.paginator import Paginator

def cadastrar_veiculo(request):
    """
    View para cadastrar um novo veículo.

    Processa requisições POST para salvar dados do formulário de veículo
    e requisições GET para exibir o formulário de cadastro.

    Args:
        request (HttpRequest): O objeto de requisição HTTP.

    Returns:
        HttpResponse: Redireciona para a página inicial após o cadastro bem-sucedido
                      ou renderiza o formulário com erros, ou um formulário vazio.
    """
    if request.method == 'POST':
        # Se a requisição for POST, processa os dados do formulário enviado.
        form = VeiculoForm(request.POST)
        if form.is_valid():
            # Se o formulário for válido, salva o novo veículo no banco de dados.
            form.save()
            messages.success(request, 'Veículo cadastrado com sucesso!')
            return redirect('index_form')  # Redireciona para a página de listagem.
        else:
            # Se o formulário for inválido, exibe mensagens de erro.
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        # Se a requisição for GET, cria um formulário vazio para exibição.
        form = VeiculoForm()
    
    # Renderiza o template de criação de veículo, passando o formulário.
    return render(request, 'form/create.html', {'form': form})

def index(request):
    """
    View para exibir a lista de veículos com funcionalidades de filtro e paginação.

    Permite filtrar veículos por país, marca, modelo e ano, e exibe os resultados
    paginados.

    Args:
        request (HttpRequest): O objeto de requisição HTTP, que pode conter parâmetros
                               de filtro e número da página.

    Returns:
        HttpResponse: Renderiza a página de índice com a lista de veículos paginada
                      e os filtros aplicados.
    """
    # Inicializa um objeto Q vazio para construir os filtros dinamicamente.
    filtros = Q()
    
    # Aplica filtros com base nos parâmetros da URL (GET request).
    # O `icontains` permite busca case-insensitive e parcial.
    if request.GET.get("pais"):
        filtros &= Q(pais__icontains=request.GET["pais"])
    if request.GET.get("brand"):
        filtros &= Q(brand__icontains=request.GET["brand"])
    if request.GET.get("modelo"):
        filtros &= Q(modelo__icontains=request.GET["modelo"])
    if request.GET.get("ano"):
        filtros &= Q(ano__icontains=request.GET["ano"])
    
    # Busca os veículos no banco de dados aplicando os filtros e ordenando-os.
    veiculos = Veiculo.objects.filter(filtros).order_by("pais", "brand", "modelo", "ano")

    # Configura a paginação para exibir 10 veículos por página.
    paginator = Paginator(object_list=veiculos, per_page=10)
    # Obtém o número da página da requisição, padrão para 1 se não especificado.
    page_number = request.GET.get("page")
    # Obtém o objeto da página atual.
    page_obj = paginator.get_page(page_number)
    
    # Renderiza o template de índice, passando os veículos paginados e os filtros.
    return render(request, "form/index.html", {
        "page_obj": page_obj,
        "filtros": request.GET, # Mantém os filtros na interface para persistência.
    })

def get_opcoes_filtro(request):
    """
    View que retorna opções de filtro (países, marcas, modelos, anos) em formato JSON.

    Filtra as opções disponíveis com base nos parâmetros de país e marca fornecidos
    na requisição GET.

    Args:
        request (HttpRequest): O objeto de requisição HTTP, que pode conter parâmetros
                               'pais' e 'marca'.

    Returns:
        JsonResponse: Um objeto JSON contendo listas distintas de países, marcas,
                      modelos e anos, baseadas nos filtros aplicados.
    """
    # Obtém os parâmetros de filtro da requisição GET, com valor padrão vazio.
    pais_param = request.GET.get(\'pais\', \'\')
    marca_param = request.GET.get(\'marca\', \'\')
    
    # Inicia a consulta com todos os veículos.
    resultados = Veiculo.objects.all()
    
    # Aplica filtros se os parâmetros correspondentes forem fornecidos.
    if pais_param:
        resultados = resultados.filter(pais__icontains=pais_param)
    if marca_param:
        resultados = resultados.filter(brand__icontains=marca_param)
    
    # Constrói o dicionário de dados com as opções distintas e ordenadas.
    data = {
        \'pais\': list(resultados.order_by(\'pais\').values_list(\'pais\', flat=True).distinct()),
        \'marcas\': list(resultados.order_by(\'brand\').values_list(\'brand\', flat=True).distinct()),
        \'modelos\': list(resultados.order_by(\'modelo\').values_list(\'modelo\', flat=True).distinct()),
        \'anos\': list(resultados.order_by(\'ano\').values_list(\'ano\', flat=True).distinct()),
    }
    # Retorna os dados como uma resposta JSON.
    return JsonResponse(data)

def update_vehicle_data(request):
    """
    View para atualizar um campo específico de um veículo via requisição POST.

    Esta função permite a atualização dinâmica de um campo de um veículo
    identificado pelo ID, recebendo o nome do campo e o novo valor.
    Utiliza `update_fields` para salvar apenas o campo modificado, otimizando a operação.

    Args:
        request (HttpRequest): O objeto de requisição HTTP, contendo 'id', 'field' e 'value'.

    Returns:
        JsonResponse: Um objeto JSON indicando o status da operação (sucesso/erro),
                      o novo valor e o valor de exibição (se houver).
    """
    if request.method == 'POST':
        veiculo_id = request.POST.get('id')
        field_name = request.POST.get('field')
        new_value = request.POST.get('value')
        
        try:
            veiculo = Veiculo.objects.get(id=veiculo_id)
            # Define o novo valor para o campo especificado.
            setattr(veiculo, field_name, new_value)
            # Salva apenas o campo modificado para otimização.
            veiculo.save(update_fields=[field_name])

            # Prepara os dados da resposta.
            response_data = {
                'status': 'success',
                'new_value': new_value,
                # Tenta obter o valor de exibição se o campo tiver choices definidos.
                'display_value': getattr(veiculo, f'get_{field_name}_display', lambda: None)()
            }

            return JsonResponse(response_data)
        except Veiculo.DoesNotExist:
            # Retorna erro se o veículo não for encontrado.
            return JsonResponse({'status': 'error', 'message': 'Veículo não encontrado'}, status=404)
        except Exception as e:
            # Captura outras exceções e retorna uma mensagem de erro genérica.
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    # Retorna erro se a requisição não for POST.
    return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)

