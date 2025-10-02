from django.shortcuts import render, redirect
from .models import Cliente
from datetime import datetime, date


def _determinar_status_suporte(cliente, hoje):
    """
    Determina o status do suporte de um cliente com base na data de vencimento.

    Args:
        cliente (Cliente): A instância do modelo Cliente.
        hoje (date): A data atual para comparação.

    Returns:
        tuple: Uma tupla contendo (status_codigo, mensagem_status).
               status_codigo: 'direito', 'vencido' ou 'vencendo'.
               mensagem_status: Uma string descritiva do status.
    """
    # Verifica se a data de vencimento é anterior à data de início do contrato
    if cliente.vencimento < cliente.data:
        return 'vencido', "SUPORTE BLOQUEADO - Não fazer atendimento - INFORMAR AO GESTOR"

    vencimento_dias = (cliente.vencimento - hoje).days

    if vencimento_dias > 30:
        return 'direito', "SUPORTE LIBERADO - Atender normalmente"
    elif vencimento_dias < 1:
        return 'vencido', "SUPORTE VENCIDO - Não fazer atendimento - BLOQUEADO"
    else:
        return 'vencendo', "SUPORTE A VENCER - Atender normalmente - Passar para o comercial"


def _obter_mensagem_atendimento(status):
    """
    Retorna uma mensagem de orientação de atendimento com base no status do suporte.

    Args:
        status (str): O código de status do suporte ('direito', 'vencido', 'vencendo').

    Returns:
        str: A mensagem de orientação para o atendimento.
    """
    if status == 'direito':
        return "Atender normalmente"
    elif status == 'vencido':
        return "Não fazer atendimento - BLOQUEADO"
    elif status == 'vencendo':
        return "Atender normalmente - Passar para o comercial"
    return ""


def buscar_serial(request):
    """
    Processa a busca por um veículo (Cliente) através do número de série.

    Esta view lida com requisições POST para buscar um serial e retorna o status
    do suporte do veículo. Se múltiplos veículos com o mesmo serial forem encontrados,
    todos são exibidos. Se nenhum for encontrado, uma mensagem de erro é exibida.

    Args:
        request (HttpRequest): O objeto da requisição HTTP.

    Returns:
        HttpResponse: Renderiza a página 'situacao/index.html' com os resultados da busca.
    """
    # Redireciona para a página inicial se a view for acessada via GET.
    if request.method != 'POST':
        return redirect('index')

    context = {}
    serial = request.POST.get('serial', '').strip()
    context['serial_digitado'] = serial

    if not serial:
        # Se o serial estiver vazio, redireciona para a página inicial.
        return redirect('index')

    clientes = Cliente.objects.filter(serial=serial)
    hoje = date.today()

    if not clientes.exists():
        # Nenhum cliente encontrado com o serial fornecido.
        context['status_message'] = 'SEM DADOS'
        context['mensagem'] = 'Nenhum veículo encontrado com este serial. Por favor, verifique o número digitado ou contate o setor comercial para atualizar o cadastro.'
        return render(request, 'situacao/index.html', context)

    if clientes.count() > 1:
        # Múltiplos clientes encontrados (duplicatas).
        lista_clientes = []
        for cliente in clientes:
            status, mensagem_status = _determinar_status_suporte(cliente, hoje)
            lista_clientes.append({
                'cliente': cliente,
                'status': status,
                'vencimento_dias': (cliente.vencimento - hoje).days,
                'status_message': mensagem_status,
            })
        
        context['clientes_duplicados'] = lista_clientes
        context['mensagem'] = 'Múltiplos veículos encontrados para este serial. Verifique os dados abaixo:'
    else:
        # Exatamente um cliente encontrado.
        cliente = clientes.first()
        status, mensagem_status = _determinar_status_suporte(cliente, hoje)
        context['cliente'] = cliente
        context['status'] = status
        context['status_message'] = mensagem_status
        context['mensagem'] = _obter_mensagem_atendimento(status)

    return render(request, 'situacao/index.html', context)


def index(request):
    """
    Renderiza a página inicial da aplicação 'situacao_veiculo'.

    Esta view é o ponto de entrada para a aplicação e exibe a página
    onde o usuário pode iniciar a busca por um serial.

    Args:
        request (HttpRequest): O objeto da requisição HTTP.

    Returns:
        HttpResponse: A página 'situacao/index.html' renderizada.
    """
    # Pode manter esta view para exibir todos os clientes inicialmente, ou apenas a interface de busca.
    return render(request, 'situacao/index.html', {'clientes': None})

