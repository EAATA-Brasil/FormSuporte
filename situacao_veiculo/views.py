from django.shortcuts import render, redirect
from .models import Cliente
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone
from django.http import JsonResponse
from django.db import IntegrityError

def buscar_serial(request):
    context = {}
    if request.method == 'POST':
        serial = request.POST.get('serial', '').strip()
        context['serial_digitado'] = serial
        
        clientes = Cliente.objects.filter(serial=serial)
        
        if not clientes.exists():
            context['status_message'] = 'SEM DADOS'
            context['mensagem'] = 'Passar para o comercial atualizar o cadastro.'
            return render(request, 'situacao/index.html', context)
        
        if clientes.count() > 1:
            lista_clientes = []
            for cliente in clientes:
                lista_clientes.append({
                    'cliente': cliente,
                    'status': cliente.status,
                    'vencimento_dias': getattr(cliente, '_vencimento_dias', None),
                    'status_message': cliente.status_message,
                })
            context['clientes_duplicados'] = lista_clientes
            context['mensagem'] = 'Encontradas múltiplas ocorrências para esse serial. Verifique os dados abaixo:'
            return render(request, 'situacao/index.html', context)
        
        cliente = clientes.first()
        context['cliente'] = cliente
        context['status'] = cliente.status

        # Se o cliente já tiver mensagem/status_message, usa elas
        if cliente.mensagem and cliente.status_message:
            context['mensagem'] = cliente.mensagem
            context['status_message'] = cliente.status_message
        else:
            # comportamento padrão
            context['mensagem'] = cliente.status_message or 'Situação não informada.'
            context['status_message'] = cliente.status_message or 'Sem status registrado.'
        
        return render(request, 'situacao/index.html', context)
    
    return redirect('index')  # GET -> homepage

def _anos_por_equipamento(equipamento: str) -> int:
    if not equipamento:
        return 2
    return 1 if 'reader' in equipamento.lower() else 2


ALLOWED_FIELDS = {"nome", "cnpj", "tel"}

def _digits_only(s: str) -> str:
    return ''.join(ch for ch in s if ch.isdigit())


@require_POST
def cadastrar_serial(request):
    data_referencia = timezone.now()

    serial = (request.POST.get('serial') or '').strip()
    nome = (request.POST.get('nome') or '').strip()
    cnpj = (request.POST.get('cnpj') or '').strip()
    tel = (request.POST.get('tel') or '').strip()
    equipamento = (request.POST.get('equipamento') or '').strip()

    field_errors = {}
    if not serial:
        field_errors['serial'] = 'Serial é obrigatório.'
    if not nome:
        field_errors['nome'] = 'Nome é obrigatório.'
    if not cnpj:
        field_errors['cnpj'] = 'CNPJ/CPF é obrigatório.'

    if field_errors:
        return JsonResponse(
            {"ok": False, "message": "Preencha os campos obrigatórios.", "field_errors": field_errors},
            status=400,
        )

    try:
        if Cliente.objects.filter(serial=serial).exists():
            return JsonResponse(
                {"ok": False, "message": "Serial já em uso.", "field_errors": {"serial": "Serial já cadastrado."}},
                status=409,
            )

        anos_para_vencimento = _anos_por_equipamento(equipamento)

        cliente = Cliente.objects.create(
            anos_para_vencimento=int(anos_para_vencimento),
            serial=serial,
            nome=nome,
            cnpj=_digits_only(cnpj) or cnpj,  # normaliza, mas preserva se não houver dígitos
            tel=tel,
            equipamento=equipamento or "N/D",
        )

        return JsonResponse(
            {
                "ok": True,
                "message": "Cadastro realizado com sucesso!",
                "data": {
                    "id": cliente.id,
                    "serial": cliente.serial,
                    "nome": cliente.nome,
                    "cnpj": cliente.cnpj,
                    "tel": cliente.tel,
                    "equipamento": cliente.equipamento,
                    "anos_para_vencimento": anos_para_vencimento,
                    "timestamp": data_referencia.isoformat(),
                },
            },
            status=201,
        )

    except IntegrityError:
        return JsonResponse(
            {"ok": False, "message": "Não foi possível cadastrar (restrição de unicidade)."},
            status=409,
        )
    except ValueError as e:
        return JsonResponse(
            {"ok": False, "message": f"Erro de validação: {e}"},
            status=400,
        )
    except Exception:
        return JsonResponse(
            {"ok": False, "message": "Erro interno ao cadastrar."},
            status=500,
        )


@require_GET
def api_buscar_cliente(request):
    serial = (request.GET.get('serial') or '').strip()
    if not serial:
        return JsonResponse({"ok": False, "message": "Informe o serial."}, status=400)

    try:
        cliente = Cliente.objects.get(serial=serial)
    except Cliente.DoesNotExist:
        return JsonResponse({"ok": False, "message": "Serial não encontrado."}, status=404)

    data = {
        "id": cliente.id,
        "serial": cliente.serial,
        "nome": cliente.nome,
        "cnpj": cliente.cnpj,
        "tel": cliente.tel
    }
    return JsonResponse({"ok": True, "data": data}, status=200)


@require_POST
def api_atualizar_cliente(request):
    serial = (request.POST.get('serial') or '').strip()
    field = (request.POST.get('field') or '').strip()
    value = (request.POST.get('value') or '')

    if not serial:
        return JsonResponse({"ok": False, "message": "Serial é obrigatório."}, status=400)
    if field not in ALLOWED_FIELDS:
        return JsonResponse({"ok": False, "message": "Campo não permitido para atualização."}, status=400)

    try:
        cliente = Cliente.objects.get(serial=serial)
    except Cliente.DoesNotExist:
        return JsonResponse({"ok": False, "message": "Serial não encontrado."}, status=404)

    # Normalizações
    if field == "cnpj":
        value = _digits_only(value) or value

    setattr(cliente, field, value)
    cliente.save(update_fields=[field])

    return JsonResponse({"ok": True, "message": "Atualizado com sucesso.", "data": {field: value}}, status=200)


def index(request):
    return render(request, 'situacao/index.html', {'clientes': None})
