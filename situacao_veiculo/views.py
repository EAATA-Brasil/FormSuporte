from datetime import date, datetime

from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_GET, require_POST
from openpyxl import load_workbook
from openpyxl.utils.datetime import from_excel

from .models import Cliente

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
                    'status_message': cliente.status_message,  # já é “efetiva”
                })
            context['clientes_duplicados'] = lista_clientes
            context['mensagem'] = 'Encontradas múltiplas ocorrências para esse serial. Verifique os dados abaixo:'
            return render(request, 'situacao/index.html', context)

        # Único cliente
        cliente = clientes.first()
        context['cliente'] = cliente
        context['status'] = cliente.status
        context['mensagem'] = cliente.message_effective   # detalhada efetiva
        context['status_message'] = cliente.status_message  # curta efetiva
        return render(request, 'situacao/index.html', context)

    return redirect('index')  # GET -> homepage

def _anos_por_equipamento(equipamento: str) -> int:
    if not equipamento:
        return 2
    return 1 if equipamento.lower().find('reader') != -1 else 2


ALLOWED_FIELDS = {"nome", "cnpj", "tel", "vencimento"}

def _digits_only(s: str) -> str:
    return ''.join(ch for ch in s if ch.isdigit())


def _parse_excel_date(value, workbook):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, (int, float)):
        try:
            return from_excel(value, epoch=workbook.epoch).date()
        except Exception:
            return None
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return None
        parsed = parse_date(cleaned)
        if parsed:
            return parsed
        try:
            return datetime.strptime(cleaned, "%d/%m/%Y").date()
        except ValueError:
            return None
    return None


@require_POST
def cadastrar_serial(request):
    data_referencia = timezone.now()

    serial = (request.POST.get('serial') or '').strip()
    nome = (request.POST.get('nome') or '').strip()
    cnpj = (request.POST.get('cnpj') or '').strip()
    tel = (request.POST.get('tel') or '').strip()
    equipamento = (request.POST.get('equipamento') or '').strip()
    data_input = (request.POST.get('data') or '').strip()

    # Novos (somente para superuser)
    anos_input = (request.POST.get('anos_para_vencimento') or '').strip()
    venc_input = (request.POST.get('vencimento') or '').strip()

    field_errors = {}
    if not serial:
        field_errors['serial'] = 'Serial é obrigatório.'

    # Validações dos novos campos (apenas se superuser enviou algo)
    anos_para_vencimento = None
    vencimento_data = None

    if request.user.is_superuser:
        # anos_para_vencimento: opcional, default 2 se não vier
        if anos_input:
            try:
                anos_para_vencimento = int(anos_input)
                if anos_para_vencimento < 0:
                    field_errors['anos_para_vencimento'] = 'Deve ser um inteiro zero ou positivo.'
            except ValueError:
                field_errors['anos_para_vencimento'] = 'Informe um número inteiro.'
        else:
            anos_para_vencimento = 2  # default solicitado

        # vencimento: opcional (pode vir vazio), valida formato se vier
        if venc_input:
            d = parse_date(venc_input)
            if not d:
                field_errors['vencimento'] = 'Data inválida (use YYYY-MM-DD).'
            else:
                vencimento_data = d

    if field_errors:
        return JsonResponse(
            {"ok": False, "message": "Corrija os campos destacados.", "field_errors": field_errors},
            status=400,
        )

    try:
        if Cliente.objects.filter(serial=serial).exists():
            return JsonResponse(
                {"ok": False, "message": "Serial já em uso.", "field_errors": {"serial": "Serial já cadastrado."}},
                status=409,
            )

        # Se não for superuser, mantém sua lógica atual (por equipamento)
        if not request.user.is_superuser:
            anos_para_vencimento = _anos_por_equipamento(equipamento)


        data_lanc = None
        if data_input:
            d = parse_date(data_input)
            if not d:
                field_errors['data'] = 'Data inválida (use YYYY-MM-DD).'
            else:
                data_lanc = d


        cliente = Cliente.objects.create(
            data=data_lanc or timezone.now(),
            anos_para_vencimento=int(anos_para_vencimento),
            serial=serial,
            nome=nome,
            cnpj=_digits_only(cnpj) or cnpj,
            tel=tel,
            equipamento=equipamento or "N/D",
            # vencimento: só setamos se superuser enviou; senão, o models.save() cuidará (auto) quando None
            vencimento=vencimento_data if request.user.is_superuser else None,
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
                    "anos_para_vencimento": cliente.anos_para_vencimento,
                    "vencimento": cliente.vencimento.isoformat() if cliente.vencimento else None,
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
        "tel": cliente.tel,
        "vencimento": cliente.vencimento.isoformat() if cliente.vencimento else None,
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

    # Normalizações específicas
    if field == "cnpj":
        value = ''.join(ch for ch in value if ch.isdigit()) or value

    if field == "vencimento":
        if not value:
            cliente.vencimento = None
            cliente.save(update_fields=["vencimento"])
            return JsonResponse({"ok": True, "message": "Vencimento removido."})
        data_v = parse_date(value)
        if not data_v:
            return JsonResponse({"ok": False, "message": "Data inválida. Use formato YYYY-MM-DD."}, status=400)
        cliente.vencimento = data_v
        cliente.save(update_fields=["vencimento"])
        return JsonResponse({"ok": True, "message": "Vencimento atualizado.", "data": {"vencimento": data_v.isoformat()}})

    setattr(cliente, field, value)
    cliente.save(update_fields=[field])

    return JsonResponse({"ok": True, "message": f"{field.capitalize()} atualizado.", "data": {field: value}})


@require_POST
def importar_excel(request):
    planilha = request.FILES.get('arquivo_excel')
    if not planilha:
        return JsonResponse({"ok": False, "message": "Envie um arquivo Excel."}, status=400)

    try:
        workbook = load_workbook(planilha, data_only=True)
    except Exception:
        return JsonResponse({"ok": False, "message": "Não foi possível ler o arquivo enviado."}, status=400)

    sheet = workbook.active
    header_cells = sheet[1]

    expected = {
        "nome cliente": "nome",
        "nome item": "equipamento",
        "serial": "serial",
        "cnpj/cpf": "cnpj",
        "contato": "tel",
        "numero emissão nf": "data",
    }

    header_map = {}
    for idx, cell in enumerate(header_cells):
        header = str(cell.value).strip().lower() if cell.value else ""
        if header in expected:
            header_map[expected[header]] = idx

    if "serial" not in header_map:
        return JsonResponse(
            {"ok": False, "message": "A coluna 'serial' é obrigatória na planilha."},
            status=400,
        )

    created = 0
    duplicates = 0
    errors = []

    for row_index, row in enumerate(sheet.iter_rows(min_row=2), start=2):
        row_data = {}
        for field, col_idx in header_map.items():
            value = row[col_idx].value if col_idx < len(row) else None
            row_data[field] = value

        if not any(row_data.values()):
            continue

        serial = (row_data.get("serial") or "").strip()
        if not serial:
            errors.append({"row": row_index, "message": "Serial ausente."})
            continue

        if Cliente.objects.filter(serial=serial).exists():
            duplicates += 1
            continue

        nome = (row_data.get("nome") or "").strip()
        equipamento = (row_data.get("equipamento") or "").strip() or "N/D"
        cnpj = _digits_only((row_data.get("cnpj") or "").strip())
        tel = (row_data.get("tel") or "").strip()

        data_valor = _parse_excel_date(row_data.get("data"), workbook)
        data_lanc = data_valor or timezone.localdate()

        try:
            Cliente.objects.create(
                data=data_lanc,
                anos_para_vencimento=_anos_por_equipamento(equipamento),
                serial=serial,
                nome=nome,
                cnpj=cnpj or None,
                tel=tel or None,
                equipamento=equipamento,
            )
            created += 1
        except IntegrityError:
            duplicates += 1
        except Exception as exc:
            errors.append({"row": row_index, "message": str(exc)})

    message = "Importação concluída."
    if created or duplicates or errors:
        message = (
            f"Importação concluída. Criados: {created}. Duplicados ignorados: {duplicates}. "
            f"Erros: {len(errors)}."
        )

    status_code = 200 if not errors else 207
    return JsonResponse(
        {"ok": True, "message": message, "data": {"created": created, "duplicates": duplicates, "errors": errors}},
        status=status_code,
    )


def index(request):
    return render(request, 'situacao/index.html', {'clientes': None})
