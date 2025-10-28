# -*- coding: utf-8 -*-
from datetime import datetime, date
from collections import defaultdict
import os
import json
import mimetypes
import requests

from langdetect import detect, DetectorFactory
DetectorFactory.seed = 0

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, Http404
from django.db.models import Q
from django.core.paginator import Paginator
from django.urls import reverse
from django.contrib.auth import authenticate, login as login_django, logout as logout_django
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.serializers import serialize
from django.db import IntegrityError
from django.http import FileResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch, mm
import io
from django.views.decorators.http import require_http_methods
import json
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
import zipfile
from django.utils.encoding import smart_str
from time import timezone
from django.utils.translation import gettext as _


from .models import Record, Country, CountryPermission, Device, ArquivoOcorrencia, Notificacao

# Constantes
DATE_COLUMNS = ["data", "deadline", "finished"]
STATUS_OCORRENCIA = {
    'Concluído': 'DONE',
    'Atrasado': 'LATE',
    'Em progresso': 'PROGRESS',
    'Requisitado': 'REQUESTED',
    'Aguardando China': 'AWAITING_CHINA',
    'China Atrasada': 'AWAITING_CHINA_LATE', # Adicionado novo status
}
STATUS_MAP_REVERSED = {v: k for k, v in STATUS_OCORRENCIA.items()}

ALLOWED_SORT_COLUMNS = [
    'feedback_manager', 'feedback_technical', 'problem_detected', 'area', 'brand',
    'country', 'data', 'deadline', 'device', 'finished', 'model', 'responsible',
    'serial', 'status', 'technical', 'version', 'year'
]

FILTERABLE_COLUMNS_FOR_OPTIONS = [
    'id','technical', 'country', 'device', 'area', 'serial', 'brand',
    'model', 'year', 'version', 'status', 'responsible',
    'data', 'deadline', 'finished'
]

URL_LOGIN = 'subir_ocorrencia'

def detectar_idioma(texto):
    if not texto or len(texto.strip()) < 3:  # textos muito curtos
        return 'PT'  # fallback
    try:
        return detect(texto).upper()  # retorna 'PT', 'ES', 'EN', etc.
    except:
        return 'PT'

def traduzir_texto(texto, target_lang='EN', api_key='SUA_CHAVE_API'):
    """
    Traduz texto curto ou longo para inglês usando DeepL Free,
    detectando automaticamente o idioma de origem.
    """
    if not texto:
        return "N/A"

    source_lang = detectar_idioma(texto)

    url = "https://api-free.deepl.com/v2/translate"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = {
        "auth_key": api_key,
        "text": texto,
        "source_lang": source_lang,
        "target_lang": target_lang,
    }

    try:
        response = requests.post(url, data=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        return result['translations'][0]['text']
    except Exception as e:
        print(f"Erro na tradução: {e}")
        return texto

def get_responsaveis():
    paises = Country.objects.all().order_by('name')
    responsaveis_por_pais = {}
    todos_responsaveis = []
    
    # Buscar o grupo "Técnicos responsáveis"
    try:
        grupo_tecnicos = Group.objects.get(name='Técnicos responsáveis')
    except Group.DoesNotExist:
        # Se o grupo não existir, retorna estruturas vazias
        return json.dumps({}), json.dumps([])
    
    # Buscar apenas usuários que são técnicos responsáveis E têm permissões de país
    usuarios_tecnicos = grupo_tecnicos.user_set.filter(
        country_permissions__isnull=False
    ).distinct().values('id', 'first_name', 'last_name', 'username')
    
    # Criar lista de todos os responsáveis (apenas técnicos)
    responsaveis_dict = {}
    for user in usuarios_tecnicos:
        nome_completo = f"{user['first_name']} {user['last_name']}".strip()
        if not nome_completo:
            nome_completo = user['username']
        
        responsavel_data = {
            'id': user['id'],
            'name': nome_completo
        }
        
        todos_responsaveis.append(responsavel_data)
        responsaveis_dict[user['id']] = responsavel_data
            
    # Mapear responsáveis por país usando CountryPermission (apenas técnicos)
    for pais in paises:
        # Buscar usuários técnicos que têm permissão neste país
        permissoes = CountryPermission.objects.filter(
            country=pais,
            user__groups=grupo_tecnicos  # Filtra apenas usuários do grupo técnicos
        ).select_related('user')
        
        responsaveis_por_pais[pais.name] = []
        for permissao in permissoes:
            user = permissao.user
            nome_completo = f"{user.first_name} {user.last_name}".strip()
            if not nome_completo:
                nome_completo = user.username
            
            responsaveis_por_pais[pais.name].append({
                'name': nome_completo,
            })
    
    responsaveis_por_pais_json = json.dumps(responsaveis_por_pais)
    todos_responsaveis_json = json.dumps(todos_responsaveis)
    return (responsaveis_por_pais_json, todos_responsaveis_json)

def subir_arquivo(files, record):
    for file in files:
        # Extrai a extensão do arquivo original
        ext = os.path.splitext(file.name)[1]  # inclui o ponto, ex: ".jpg"

        # Define o novo nome do arquivo
        novo_nome = file.name

        # Cria o registro no banco
        ArquivoOcorrencia.objects.create(
            record=record,
            arquivo=file,
            nome_original=novo_nome  # ou mantenha file.name se preferir
        )

@login_required(login_url=URL_LOGIN)
def download_todos_arquivos(request, record_id):
    record = get_object_or_404(Record, id=record_id)
    arquivos = ArquivoOcorrencia.objects.filter(record=record)

    print(arquivos)

    if not arquivos.exists():
        return JsonResponse({'status': 'error', 'message': 'Nenhum arquivo encontrado.'}, status=404)

    if arquivos.count() <= 1:
        # Retorna múltiplos arquivos, mas um por vez via response streaming
        # (normalmente o ideal é baixar em ZIP também, mas mantendo a regra)
        arquivo = arquivos.first()
        response = FileResponse(arquivo.arquivo.open("rb"), as_attachment=True, filename=arquivo.nome_original)
        return response
    else:
        # Gera o zip temporário
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            for arq in arquivos:
                zip_file.write(arq.arquivo.path, arcname=arq.nome_original)
        zip_buffer.seek(0)

        response = HttpResponse(zip_buffer, content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename=arquivos_ocorrencia_{record.id}.zip'
        return response


@login_required(login_url=URL_LOGIN)
def index(request):
    responsaveis_por_pais_json, todos_responsaveis_json = get_responsaveis()
    
    ocorrencias_queryset = Record.objects.all()
    user = request.user

    if not user.is_superuser:
        paises_permitidos_ids = CountryPermission.objects.filter(user=user).values_list('country_id', flat=True)
        is_semi_admin = user.groups.filter(name='Semi Admin').exists()

        if is_semi_admin:
            ocorrencias_queryset = ocorrencias_queryset.filter(country_id__in=list(paises_permitidos_ids))
        else:
            nome_completo_usuario = f"{user.first_name} {user.last_name}".strip() or user.username
            ocorrencias_queryset = ocorrencias_queryset.filter(
                Q(country_id__in=list(paises_permitidos_ids)) & 
                Q(responsible=nome_completo_usuario)
            )

    status_map = {
        Record.STATUS_OCORRENCIA.DONE: _("Concluído"),
        Record.STATUS_OCORRENCIA.LATE: _("Atrasado"),
        Record.STATUS_OCORRENCIA.PROGRESS: _("Em progresso"),
        Record.STATUS_OCORRENCIA.REQUESTED: _("Requisitado"),
        Record.STATUS_OCORRENCIA.AWAITING_CHINA: _("Aguardando China"),
        Record.STATUS_OCORRENCIA.AWAITING_CHINA_LATE: _("China Atrasada"),

    }

    ocorrencias_dict = defaultdict(lambda: {label: 0 for label in status_map.values()})

    for record in ocorrencias_queryset.values('responsible', 'status'):
        nome = record['responsible']
        status_codigo = record['status']
        status_legivel = status_map.get(status_codigo)

        if nome and nome != "Não identificado" and status_legivel:
            ocorrencias_dict[nome][status_legivel] += 1

    ocorrencias_json = json.dumps(ocorrencias_dict, ensure_ascii=False)

    # --- INÍCIO DA ALTERAÇÃO NECESSÁRIA ---

    is_super = user.is_superuser
    # 1. Reutiliza a verificação de 'is_semi_admin' que já fizemos
    is_semi_admin = user.groups.filter(name='Semi Admin').exists() 
    
    # 2. Cria a nova variável de permissão
    has_edit_permission = is_super or is_semi_admin

    # --- FIM DA ALTERAÇÃO NECESSÁRIA ---

    permitted_countries = Country.objects.filter(
        id__in=CountryPermission.objects.filter(user=user).values_list('country_id', flat=True)
    ).values_list('name', flat=True) if not is_super else Country.objects.all().values_list('name', flat=True)

    context = {
        'user': user,
        'paises_permitidos': list(permitted_countries),
        'has_full_permission': is_super,
        
        # 3. Adiciona a nova variável ao contexto para ser usada no template
        'has_edit_permission': has_edit_permission,
        
        'responsaveis_por_pais': responsaveis_por_pais_json,
        'todos_responsaveis': todos_responsaveis_json,
        'ocorrencias_json': ocorrencias_json,
    }
    return render(request, 'ocorrencia/index.html', context)

@login_required(login_url=URL_LOGIN)
def filter_data_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            filters = data.get('filters', {})
            sort_info = data.get('sort', {'column': 'data', 'direction': 'asc'})
            page_number = data.get('page', 1)

            # 1. Consulta base otimizada
            base_queryset = Record.objects.select_related('device', 'country')
            
            user = request.user
            
            # --- INÍCIO DA DEPURAÇÃO ---
            print(f"--- Iniciando depuração para o usuário: {user.username} ---")
            
            if not user.is_superuser:
                # 1. Quais países este usuário pode ver?
                paises_permitidos_ids = CountryPermission.objects.filter(user=user).values_list('country_id', flat=True)
                paises_permitidos_lista = list(paises_permitidos_ids)
                print(f"IDs dos países permitidos: {paises_permitidos_lista}")

                # 2. O usuário é Semi Admin?
                is_semi_admin = user.groups.filter(name='Semi Admin').exists()
                print(f"É Semi Admin? {is_semi_admin}")
                
                # 3. Quais são TODOS os grupos do usuário?
                grupos_usuario = list(user.groups.all().values_list('name', flat=True))
                print(f"Grupos do usuário: {grupos_usuario}")

                if is_semi_admin:
                    print("Lógica de Semi Admin ativada. Filtrando por países...")
                    base_queryset = base_queryset.filter(country_id__in=paises_permitidos_lista)
                else:
                    print("Lógica de Técnico Padrão ativada. Filtrando por países E responsável...")
                    nome_completo_usuario = f"{user.first_name} {user.last_name}".strip() or user.username
                    print(f"Filtrando por responsável: '{nome_completo_usuario}'")
                    base_queryset = base_queryset.filter(
                        Q(country_id__in=paises_permitidos_lista) & 
                        Q(responsible=nome_completo_usuario)
                    )
                
                print(f"Total de registros após filtro de permissão: {base_queryset.count()}")
            else:
                print("Usuário é Superuser. Nenhuma permissão aplicada.")
            
            print("--- Fim da depuração ---")
            # --- FIM DA DEPURAÇÃO ---

            queryset = base_queryset
            
            # 2. Construção dos filtros selecionados pelo usuário na interface
            q_objects = Q()
            for column, values in filters.items():
                if not isinstance(values, list) or not values:
                    continue

                column_q = Q()
                has_empty = '' in values
                non_empty = [v.strip() for v in values if v != ""]

                TEXT_CASE_INSENSITIVE_COLUMNS = [
                    'codigo_externo', 'technical', 'area', 'serial', 'brand', 'model',
                    'version', 'responsible', 'problem_detected', 'feedback_technical',
                    'feedback_manager'
                ]

                # Filtros para valores não vazios
                if non_empty:
                    if column == 'status':
                        status_values = [STATUS_OCORRENCIA.get(v, v) for v in non_empty]
                        # Adiciona AWAITING_CHINA ao filtro se AWAITING for selecionado
                        if 'AWAITING' in status_values and 'AWAITING_CHINA' not in status_values:
                            status_values.append('AWAITING_CHINA')
                        column_q |= Q(status__in=status_values)
                    elif column in DATE_COLUMNS:
                        dates = []
                        for v in non_empty:
                            try:
                                if '/' in v:
                                    dt = datetime.strptime(v, '%d/%m/%Y').date()
                                else:
                                    dt = datetime.strptime(v, '%Y-%m-%d').date()
                                dates.append(dt)
                            except:
                                continue
                        if dates:
                            column_q |= Q(**{f'{column}__in': dates})
                    elif column == 'country':
                        country_q_objects = Q()
                        for val in non_empty:
                            country_q_objects |= Q(country__name__iexact=val.strip())
                        column_q |= country_q_objects
                    elif column == 'device':
                        device_q_objects = Q()
                        for val in non_empty:
                            device_q_objects |= Q(device__name__iexact=val.strip())
                        column_q |= device_q_objects
                    elif column in TEXT_CASE_INSENSITIVE_COLUMNS:
                        text_q_objects = Q()
                        for val in non_empty:
                            text_q_objects |= Q(**{f'{column}__icontains': val.strip()})
                        column_q |= text_q_objects
                    else:
                        column_q |= Q(**{f'{column}__in': non_empty})

                # Filtro para valores vazios/nulos
                if has_empty:
                    if column == 'country':
                        column_q |= Q(country__isnull=True)
                    elif column == 'device':
                        column_q |= Q(device__isnull=True)
                    elif column == 'codigo_externo':
                        column_q |= Q(codigo_externo__isnull=True)
                    else:
                        column_q |= Q(**{f'{column}__isnull': True}) | Q(**{f'{column}__exact': ''})

                if column_q:
                    q_objects &= column_q

            if q_objects:
                queryset = queryset.filter(q_objects)

            # 3. Ordenação
            sort_column = sort_info.get('column', 'data')
            sort_direction = sort_info.get('direction', 'asc')
            
            if sort_column in ALLOWED_SORT_COLUMNS:
                if sort_column == 'country':
                    order_field = f"{'-' if sort_direction == 'desc' else ''}country__name"
                elif sort_column == 'device':
                    order_field = f"{'-' if sort_direction == 'desc' else ''}device__name"
                else:
                    order_field = f"{'-' if sort_direction == 'desc' else ''}{sort_column}"
                queryset = queryset.order_by(order_field)

            # 4. Paginação
            paginator = Paginator(queryset, 13)
            page_obj = paginator.get_page(page_number)

            # 5. Preparação dos dados para a resposta JSON
            records_data = []
            for record in page_obj.object_list:
                record_data = {
                    'id': record.id,
                    'codigo_externo': record.codigo_externo or str(record.id),
                    'data': record.data,
                    'technical': record.technical or '',
                    'country': record.country.name if record.country else '',
                    
                    # --- ADICIONE ESTA LINHA ---
                    'country_id': record.country.id if record.country else None,
                    'is_awaiting_china_late': record.is_awaiting_china_late(),
                    # -------------------------

                    'device': record.device.name if record.device else '',
                    'area': record.area or '',
                    'serial': record.serial or '',
                    'vin': record.vin or '',
                    'tipo_ecu': record.tipo_ecu or '',
                    'tipo_motor': record.tipo_motor or '',
                    'brand': record.brand or '',
                    'model': record.model or '',
                    'contact': record.contact or '',
                    'year': record.year or '',
                    'version': record.version or '',
                    'problem_detected': record.problem_detected or '',
                    'status': STATUS_MAP_REVERSED.get(record.status, record.status or ''),

                    'status_display': STATUS_MAP_REVERSED.get(record.status, record.status or ''),
                    'status_code': record.status,

                    'deadline': record.deadline.strftime('%d/%m/%Y') if record.deadline else '',
                    'responsible': record.responsible or '',
                    'finished': record.finished.strftime('%d/%m/%Y') if record.finished else '',
                    'arquivos': [
                        {
                            'id': arquivo.id,
                            'record_id': arquivo.record.codigo_externo or str(arquivo.record_id),
                            'url': arquivo.arquivo.url,
                            'nome_original': arquivo.nome_original
                        }
                        for arquivo in ArquivoOcorrencia.objects.filter(record=record)
                    ],
                }
                record_data['status'] = record_data['status_display']
                records_data.append(record_data)

            # 6. Geração de opções de filtro dinâmicas
            FILTERABLE_COLUMNS_FOR_OPTIONS = [
                'codigo_externo', 'technical', 'country', 'device', 'area', 'serial', 'brand',
                'model', 'year', 'version', 'status', 'responsible',
                'data', 'deadline', 'finished'
            ]

            filter_options = {}
            # IMPORTANTE: As opções de filtro são geradas a partir do `queryset` que já foi
            # filtrado por permissão, garantindo que o usuário só veja opções relevantes.
            for col in FILTERABLE_COLUMNS_FOR_OPTIONS:
                if col == 'country':
                    options = queryset.exclude(country__isnull=True).values_list('country__name', flat=True).distinct()
                    filter_options[col] = sorted(list(set([opt.upper() for opt in options if opt])))
                elif col == 'device':
                    options = queryset.exclude(device__isnull=True).values_list('device__name', flat=True).distinct()
                    filter_options[col] = sorted(list(set([opt.upper() for opt in options if opt])))
                elif col == 'status':
                    status_values = queryset.values_list('status', flat=True).distinct()
                    filter_options[col] = sorted(
                        [STATUS_MAP_REVERSED.get(opt, opt) for opt in status_values if opt],
                        key=lambda x: list(STATUS_OCORRENCIA.keys()).index(x) if x in STATUS_OCORRENCIA else float('inf')
                    )
                elif col in DATE_COLUMNS:
                    dates = queryset.exclude(**{f'{col}__isnull': True}).values_list(col, flat=True).distinct()
                    date_tree = defaultdict(lambda: defaultdict(list))
                    for dt in dates:
                        if dt:
                            try:
                                dt = dt if isinstance(dt, date) else datetime.strptime(str(dt), '%Y-%m-%d').date()
                                year = str(dt.year)
                                month = dt.strftime('%m')
                                day = dt.strftime('%d')
                                if day not in date_tree[year][month]:
                                    date_tree[year][month].append(day)
                            except:
                                continue
                    for year in date_tree:
                        for month in date_tree[year]:
                            date_tree[year][month] = sorted(date_tree[year][month])
                        date_tree[year] = dict(sorted(date_tree[year].items()))
                    filter_options[col] = dict(sorted(date_tree.items()))
                elif col == 'codigo_externo':
                    options = queryset.values_list(col, flat=True).distinct()
                    filter_options[col] = sorted(list(set([opt for opt in options if opt is not None])))
                else:
                    options = queryset.exclude(**{f'{col}__isnull': True}).exclude(**{f'{col}__exact': ''}).values_list(col, flat=True).distinct()
                    filter_options[col] = sorted(list(set([opt.upper() for opt in options if opt is not None])))

            # 7. Resposta final
            return JsonResponse({
                'records': records_data,
                'filter_options': filter_options,
                'num_pages': paginator.num_pages,
                'current_page': page_obj.number,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método inválido'}, status=405)

def logout_view(request):
    logout_django(request)
    return redirect('subir_ocorrencia')


def login_view(request):
    if request.method == "GET":
        next_url = request.GET.get('next', None)
        context = {'next': next_url} if next_url else {}
        return render(request, 'ocorrencia/login.html', context)

    else:
        username = request.POST.get('country', '').strip().capitalize()
        password = request.POST.get('password', '')
        next_url = request.POST.get('next', None)

        user = authenticate(request, username=username, password=password)
        if user is None:
            user = authenticate(request, username=username.upper(), password=password)

        if user:
            login_django(request, user)
            return redirect(next_url) if next_url else redirect('/ocorrencia')
        else:
            messages.error(request, "Usuário ou senha inválidos.")
            return redirect(reverse('login_ocorrencias'))


@login_required(login_url=URL_LOGIN)
def criar_usuario(request):
    if not request.user.is_superuser:
        messages.error(request, "Você precisa ser superusuário para criar usuários.")
        return redirect('/ocorrencia')

    paises_existentes = Country.objects.all().order_by('name')

    if request.method == "GET":
        return render(request, 'ocorrencia/criar_usuario.html', {'paises': paises_existentes})

    if request.method == "POST":
        username = request.POST.get('username', '').strip().capitalize()
        password = request.POST.get('password', '')
        # O valor 'semi_admin' agora pode vir do formulário
        tipo_usuario = request.POST.get('tipo_usuario', 'responsavel') 
        paises_responsavel = request.POST.getlist('paises_responsavel')

        if not username or not password:
            messages.error(request, "Nome de usuário e senha obrigatórios.")
            return redirect('criar_usuario')

        if User.objects.filter(username=username).exists():
            messages.warning(request, "Usuário já existe.")
            return redirect('criar_usuario')

        # Criar o usuário
        user = User.objects.create_user(username=username, password=password)
        
        # Adicionar o usuário ao grupo correspondente
        try:
            # ======================================================
            # INÍCIO DA ALTERAÇÃO: Lógica para os grupos
            # ======================================================
            if tipo_usuario == 'responsavel':
                nome_grupo = 'Técnicos responsáveis'
            elif tipo_usuario == 'reporte':
                nome_grupo = 'Técnicos de reporte'
            elif tipo_usuario == 'semi_admin':
                # O nome do grupo deve ser exatamente este para a lógica de permissão funcionar
                nome_grupo = 'Semi Admin'
            else:
                # Um fallback seguro, caso algo inesperado aconteça
                nome_grupo = 'Técnicos de reporte'

            # Busca ou cria o grupo e adiciona o usuário a ele
            grupo, created = Group.objects.get_or_create(name=nome_grupo)
            user.groups.add(grupo)
            # ======================================================
            # FIM DA ALTERAÇÃO
            # ======================================================

        except Exception as e:
            # Se der erro, o usuário ainda é criado, mas informamos sobre o problema no grupo
            messages.warning(request, f"Usuário criado, mas houve um erro ao adicionar ao grupo: {str(e)}")
        
        # Adicionar permissões de países (funciona para todos os tipos de usuário)
        for pais_id in paises_responsavel:
            try:
                country = Country.objects.get(id=pais_id)
                CountryPermission.objects.create(user=user, country=country)
            except Country.DoesNotExist:
                continue

        messages.success(request, f"Usuário {username} criado com sucesso como {tipo_usuario}.")
        return redirect('criar_usuario')

# @login_required(login_url='subir_ocorrencia')
def subir_ocorrencia(request):
    has_full_permission = request.user.is_superuser
    paises = Country.objects.all().order_by('name')
    responsaveis_por_pais = {}
    todos_responsaveis = []
    todos_equipamentos = []
    nome_responsaveis = []
    # Buscar os dois grupos
    grupo_responsaveis = Group.objects.filter(name='Técnicos responsáveis').first()

    # Prepara lista de responsáveis (usuários de QUALQUER UM dos dois grupos)
    usuarios_query = User.objects.all()
    
    # Filtra usuários que estão em pelo menos um dos grupos
    if  grupo_responsaveis:
        from django.db.models import Q
        query_filter = Q()
        if grupo_responsaveis:
            query_filter |= Q(groups=grupo_responsaveis)
        
        usuarios_com_permissao = usuarios_query.filter(query_filter).distinct().values('id', 'first_name', 'last_name', 'username')
    else:
        usuarios_com_permissao = []

    for user in usuarios_com_permissao:
        nome_completo = f"{user['first_name']} {user['last_name']}".strip()
        if not nome_completo:
            nome_completo = user['username']
        todos_responsaveis.append({'id': user['id'], 'name': nome_completo})
        nome_responsaveis.append(nome_completo)
        

    # Prepara lista de equipamentos
    todos_equipamentos = list(Device.objects.all().values('id', 'name'))

    # Mapeia responsáveis por país (usuários de qualquer um dos dois grupos)
    for pais in paises:
        responsaveis_por_pais[pais.id] = []
        
        # Filtra CountryPermission pelos usuários dos grupos
        permissoes_query = CountryPermission.objects.filter(country=pais)
        
        if grupo_responsaveis:
            from django.db.models import Q
            user_filter = Q()
            if grupo_responsaveis:
                user_filter |= Q(user__groups=grupo_responsaveis)
            
            permissoes_query = permissoes_query.filter(user_filter).distinct()
        
        for permissao in permissoes_query.select_related('user'):
            user = permissao.user
            nome_completo = f"{user.first_name} {user.last_name}".strip() or user.username
            responsaveis_por_pais[pais.id].append({'id': user.id, 'name': nome_completo})

    if request.method == 'POST':
        try:
            # Validações obrigatórias
            required_fields = {
                'country': 'País',
                'device': 'Equipamento',
                'technical': 'Técnico',
                'serial': 'Serial',
                'brand': 'Marca',
                'model': 'Modelo',
                'year': 'Ano',
                'version': 'Versão',
                'problem_detected': 'Problema Detectado'
            }

            missing_fields = [field_name for field_name, field_label in required_fields.items() 
                             if not request.POST.get(field_name)]
            if missing_fields:
                return JsonResponse({
                    "status": "error",
                    "message": f"Campos obrigatórios faltando: {', '.join([required_fields[f] for f in missing_fields])}"
                }, status=400)

            country = get_object_or_404(Country, id=request.POST.get("country"))
            device = get_object_or_404(Device, id=request.POST.get("device"))

            # Validação específica do ticket

            # ----------------------------------------------------------------------------------
            # VALIDAÇÃO THINKCAR: O serial DEVE obedecer ao padrão regex fornecido.
            # ----------------------------------------------------------------------------------
            serial_input = request.POST.get("serial", "").strip().upper()
            device_name = device.name.upper() # Obtém o nome do equipamento selecionado
            
            # Padrão regex para Thinkcar: 12 dígitos OU "9TDP" seguido de 8 caracteres alfanuméricos
            THINKCAR_REGEX = r"^(?:\d{12}|9TDP[A-Z0-9]{8})$"
            
            if "THINKCAR" in device_name or "READER" in device_name:
                import re
                if not re.match(THINKCAR_REGEX, serial_input):
                    return JsonResponse({
                        "status": "error",
                        "message": "Serial inválido para equipamento Thinkcar. O serial deve ter 12 dígitos ou começar com '9TDP' seguido de 8 caracteres alfanuméricos."
                    }, status=400)
            # ----------------------------------------------------------------------------------
            ticket = request.POST.get("ticket", "").strip()
            if ticket:
                if len(ticket) > 20:
                    return JsonResponse({
                        "status": "error",
                        "message": "Ticket deve ter no máximo 20 caracteres."
                    }, status=400)
                
                if Record.objects.filter(codigo_externo=ticket).exists():
                    return JsonResponse({
                        "status": "error",
                        "message": "Este ticket já está em uso. Insira um código único."
                    }, status=400)

            # Prepara dados do registro
            record_data = {
                'technical': request.POST.get("technical"),
                'responsible': request.POST.get("responsible"),
                'device': device,
                'area': request.POST.get("area_radio"),
                'serial': request.POST.get("serial"),
                'vin': request.POST.get("vin"),
                'brand': request.POST.get("brand"),
                'model': request.POST.get("model"),
                'contact': request.POST.get("contact"),
                'year': request.POST.get("year"),
                'country': country,
                'version': request.POST.get("version"),
                'problem_detected': request.POST.get("problem_detected"),
                'tipo_ecu': request.POST.get("tipo_ecu"),
                'tipo_motor': request.POST.get("tipo_motor"),
                'status': Record.STATUS_OCORRENCIA.REQUESTED
            }

            if ticket:
                record_data['codigo_externo'] = ticket

            # Validação de status
            status_input = request.POST.get("status", "Requisitado")
            status_mapping = {
                'Requisitado': Record.STATUS_OCORRENCIA.REQUESTED,
                'Concluído': Record.STATUS_OCORRENCIA.DONE,
                'Em progresso': Record.STATUS_OCORRENCIA.PROGRESS,
                'Atrasado': Record.STATUS_OCORRENCIA.LATE,
                'Aguardando China': Record.STATUS_OCORRENCIA.AWAITING_CHINA,
            }
            if status_input in status_mapping:
                record_data['status'] = status_mapping[status_input]

            # Validação de deadline
            if request.POST.get("deadline"):
                try:
                    record_data['deadline'] = datetime.strptime(
                        request.POST.get("deadline"), 
                        '%d/%m/%Y'
                    ).date()
                except ValueError:
                    return JsonResponse({
                        "status": "error",
                        "message": "Formato de data inválido. Use DD/MM/AAAA."
                    }, status=400)

            # Cria o registro
            technical = request.POST.get("technical").capitalize()
            print(technical)

            # Extrai apenas os nomes da lista de dicionários
            nomes_responsaveis_pais = [r['name'] for r in responsaveis_por_pais[pais.id]]
            if not has_full_permission:
                if technical in nome_responsaveis and technical in nomes_responsaveis_pais:
                    record_data['responsible'] = request.POST.get("technical").capitalize()
            try:
                record = Record.objects.create(**record_data)
            except IntegrityError as e:
                return JsonResponse({
                    "status": "error",
                    "message": "Erro ao criar registro. Verifique os dados."
                }, status=400)

            # Processa arquivos anexados
            for file in request.FILES.getlist("arquivo"):
                ArquivoOcorrencia.objects.create(
                    record=record,
                    arquivo=file,
                    nome_original=file.name
                )

            return JsonResponse({
                "status": "success",
                "message": "Ocorrência registrada com sucesso!",
                "record_id": record.id
            }, status=201)

        except Country.DoesNotExist:
            return JsonResponse({
                "status": "error",
                "message": "País selecionado não existe."
            }, status=400)
        except Device.DoesNotExist:
            return JsonResponse({
                "status": "error", 
                "message": "Equipamento selecionado não existe."
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": f"Erro interno: {str(e)}"
            }, status=500)

    # GET request - prepara dados para o template
    paises_dict = {str(p.id): p.name for p in paises}

    # se for GET normal (primeiro carregamento)
    context = {
        'paises': paises,
        'paises_json': json.dumps(paises_dict),
        'has_full_permission': has_full_permission,
        'responsaveis_por_pais': json.dumps(responsaveis_por_pais),
        'todos_responsaveis': json.dumps(todos_responsaveis),
        'todos_equipamentos_raw': todos_equipamentos,
    }

    # só envia username se o usuário estiver autenticado E ainda não houver um POST que o altere
    if request.method == 'GET' and request.user.is_authenticated:
        context['username'] = request.user.username

    return render(request, 'ocorrencia/subir_ocorrencia.html', context)
# Views auxiliares para AJAX (opcionais)
def get_responsaveis_por_pais(request):
    """
    View para retornar responsáveis filtrados por país via AJAX
    """
    country_id = request.GET.get('country_id')
    
    if country_id:
        try:
            country = Country.objects.get(id=country_id)
            # Buscar responsáveis que têm permissão neste país
            permissoes = CountryPermission.objects.filter(country=country).select_related('user')
            
            responsaveis_list = []
            for permissao in permissoes:
                user = permissao.user
                nome_completo = f"{user.first_name} {user.last_name}".strip()
                if not nome_completo:
                    nome_completo = user.username
                
                responsaveis_list.append({
                    'id': user.id,
                    'name': nome_completo
                })
        except Country.DoesNotExist:
            responsaveis_list = []
    else:
        # Retornar todos os responsáveis
        usuarios_com_permissao = User.objects.filter(
            country_permissions__isnull=False
        ).distinct().values('id', 'first_name', 'last_name', 'username')
        
        responsaveis_list = []
        for user in usuarios_com_permissao:
            nome_completo = f"{user['first_name']} {user['last_name']}".strip()
            if not nome_completo:
                nome_completo = user['username']
            
            responsaveis_list.append({
                'id': user['id'],
                'name': nome_completo
            })
    
    return JsonResponse({'responsaveis': responsaveis_list})


def get_paises_por_responsavel(request):
    """
    View para retornar países filtrados por responsável via AJAX
    """
    responsavel_id = request.GET.get('responsavel_id')
    
    if responsavel_id:
        try:
            user = User.objects.get(id=responsavel_id)
            # Buscar países para os quais este usuário tem permissão
            permissoes = CountryPermission.objects.filter(user=user).select_related('country')
            
            paises_list = []
            for permissao in permissoes:
                paises_list.append({
                    'id': permissao.country.id,
                    'name': permissao.country.name
                })
        except User.DoesNotExist:
            paises_list = []
    else:
        # Retornar todos os países
        paises_list = list(Country.objects.all().values('id', 'name'))
    
    return JsonResponse({'paises': paises_list})

# Em seu arquivo views.py

@login_required(login_url=URL_LOGIN)
def alterar_dados(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método inválido'}, status=405)

    try:
        # Lógica para upload de arquivos (multipart/form-data)
        if request.content_type.startswith('multipart/form-data'):
            # ... (sua lógica de upload de arquivos permanece a mesma, não precisa mudar)
            body = request.POST
            files = request.FILES.getlist("arquivo")

            if body.get("action") == "deletar":
                file_id = body.get("file")
                try:
                    arquivo = ArquivoOcorrencia.objects.get(id=file_id)
                    arquivo.delete()
                    return JsonResponse({'status': 'success'})
                except ArquivoOcorrencia.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': 'Arquivo não encontrado'}, status=404)

            elif files:
                try:
                    record = Record.objects.get(id=body.get('record'))
                    for file in files:
                        ArquivoOcorrencia.objects.create(
                            record=record,
                            arquivo=file,
                            nome_original=file.name
                        )
                    return JsonResponse({'status': 'success', 'page_num': body.get("page_num")})
                except Exception as e:
                    return JsonResponse({'status': 'error','message': f'Erro ao salvar arquivos: {str(e)}'}, status=500)
            
            # Se não for nenhuma das ações acima, retorna erro.
            return JsonResponse({'status': 'error', 'message': 'Ação multipart inválida'}, status=400)

        # Lógica para JSON puro (atualização de campos)
        # Lógica para JSON (atualização de campos)
        else:
            data = json.loads(request.body.decode('utf-8'))
            record = get_object_or_404(Record, id=data.get('id'))
            field_name = data.get('field')
            new_value = data.get('value')
            new_display = str(new_value)
            if field_name == 'finished' and not new_value:
                record.clear_finished_date()  # Usa o método especial
                new_display = ''
            elif field_name == 'deadline' and not new_value:
                record.clear_deadline_date()  # Usa o método especial
                new_display = ''
                
            elif field_name == 'country':
                if new_value == 'revert':
                    original_country_name = record.country_original
                    record.country = Country.objects.filter(name=original_country_name).first()
                    new_display = original_country_name or ''
                else:
                    country_obj = get_object_or_404(Country, id=new_value)
                    record.country = country_obj
                    new_display = country_obj.name
            
            elif field_name in DATE_COLUMNS and new_value:
                parsed_date = datetime.strptime(new_value, '%d/%m/%Y').date()
                setattr(record, field_name, parsed_date)
                new_display = parsed_date.strftime('%Y-%m-%d')
            
            else:
                setattr(record, field_name, new_value)
                new_display = new_value

            # SALVA O REGISTRO UMA ÚNICA VEZ.
            # O modelo (models.py) irá aplicar toda a lógica de status necessária.
            record.save()

            if field_name == 'feedback_manager' and new_value and str(new_value).strip():
                criar_notificacao_feedback(record, 'feedback_manager', request.user)
            
            return JsonResponse({
                'status': 'success',
                'new_display': new_display,
                'page_num': data.get("page_num")
            })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

# Alias para compatibilidade
update_record_view = alterar_dados


@login_required(login_url=URL_LOGIN)
def download_arquivo(request, arquivo_id):
    """
    View para download seguro de arquivos anexados às ocorrências
    """
    try:
        # Busca o arquivo no banco de dados
        arquivo = get_object_or_404(ArquivoOcorrencia, id=arquivo_id)
        
        # Verifica se o usuário tem permissão para acessar este arquivo
        # (baseado nas permissões de país da ocorrência)
        record = arquivo.record
        user = request.user
        
        if not user.is_superuser:
            # Verifica se o usuário tem permissão para o país da ocorrência
            if record.country:
                has_permission = CountryPermission.objects.filter(
                    user=user,
                    country=record.country
                ).exists()
                if not has_permission:
                    raise Http404("Arquivo não encontrado ou sem permissão")
        
        # Caminho completo do arquivo
        file_path = arquivo.arquivo.path
        
        # Verifica se o arquivo existe fisicamente
        if not os.path.exists(file_path):
            raise Http404("Arquivo não encontrado no sistema")
        
        # Determina o tipo MIME do arquivo
        content_type, _ = mimetypes.guess_type(file_path)
        if content_type is None:
            content_type = 'application/octet-stream'
        
        # Lê o arquivo
        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type=content_type)
        
        # Define o cabeçalho para forçar download
        filename = arquivo.nome_original or os.path.basename(file_path)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except ArquivoOcorrencia.DoesNotExist:
        raise Http404("Arquivo não encontrado")
    except Exception as e:
        # Log do erro (em produção, usar logging adequado)
        print(f"Erro no download do arquivo {arquivo_id}: {str(e)}")
        raise Http404("Erro ao processar download")

def get_record(request, pk):
    try:
        record = Record.objects.prefetch_related('arquivos').get(id=pk)
        
        data = {
            "id": record.id,
            "technical": record.technical,
            "responsible": record.responsible,
            "device": str(record.device) if record.device else None,
            "area": record.area,
            "serial": record.serial,
            'tipo_ecu': record.tipo_ecu,
            'tipo_motor': record.tipo_motor,
            "vin": record.vin,
            "brand": record.brand,
            "model": record.model,
            "contact": record.contact,
            "year": record.year,
            "version": record.version,
            "country": record.country.name if record.country else None,
            "status": record.status,
            "data": record.data.strftime("%Y-%m-%d") if record.data else None,
            "deadline": record.deadline.strftime("%Y-%m-%d") if record.deadline else None,
            "finished": record.finished.strftime("%Y-%m-%d") if record.finished else None,
            "problem_detected": record.problem_detected,
            "feedback_technical": record.feedback_technical,
            "feedback_manager": record.feedback_manager,
            "arquivos": [
                {
                    "id": arquivo.id,
                    "nome_original": arquivo.nome_original,
                    "caminho": arquivo.arquivo.url if arquivo.arquivo else None
                }
                for arquivo in record.arquivos.all()
            ]
        }

        return JsonResponse(data)

    except Record.DoesNotExist:
        return JsonResponse({'error': 'Registro não encontrado'}, status=404)


def criar_notificacao_feedback(record, tipo_feedback, gestor_user):
    """
    Cria uma notificação quando um gestor adiciona feedback a uma ocorrência
    """
    try:
        # Buscar o usuário responsável pela ocorrência
        if record.responsible and record.responsible != "Não identificado":
            # Tentar encontrar o usuário pelo nome completo ou username
            usuarios_responsaveis = User.objects.filter(
                Q(first_name__icontains=record.responsible.split()[0]) |
                Q(username__icontains=record.responsible) |
                Q(last_name__icontains=record.responsible.split()[-1] if len(record.responsible.split()) > 1 else record.responsible)
            )
            
            for usuario in usuarios_responsaveis:
                # Evitar criar notificação para o próprio gestor que fez o feedback
                if usuario.id != gestor_user.id:
                    # Verificar se já existe uma notificação não lida para esta ocorrência e usuário
                    notificacao_existente = Notificacao.objects.filter(
                        user=usuario,
                        record=record,
                        tipo=tipo_feedback,
                        lida=False
                    ).first()
                    
                    if not notificacao_existente:
                        # Criar nova notificação
                        titulo = f"Nova mensagem na ocorrência #{record.codigo_externo or record.id}"
                        resumo = f"{record.responsible} mandou uma nova mensagem"
                        
                        Notificacao.objects.create(
                            user=usuario,
                            record=record,
                            tipo=tipo_feedback,
                            titulo=titulo,
                            resumo=resumo
                        )
    except Exception as e:
        print(f"Erro ao criar notificação: {e}")

@login_required(login_url=URL_LOGIN)
def listar_notificacoes(request):
    """
    API para listar notificações não lidas do usuário logado
    """
    try:
        notificacoes = Notificacao.objects.filter(
            user=request.user,
            lida=False
        ).select_related('record', 'record__device').order_by('-criada_em')
        
        notificacoes_data = []
        for notificacao in notificacoes:
            notificacoes_data.append({
                'id': notificacao.id,
                'titulo': notificacao.titulo,
                'resumo': notificacao.resumo,
                'tipo': notificacao.tipo,
                'criada_em': notificacao.criada_em.strftime('%d/%m/%Y %H:%M'),
                'record_id': notificacao.record.id,
                'record_codigo': notificacao.record.codigo_externo or str(notificacao.record.id)
            })
        
        return JsonResponse({
            'status': 'success',
            'notificacoes': notificacoes_data,
            'total': len(notificacoes_data)
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required(login_url=URL_LOGIN)
def marcar_notificacao_lida(request, notificacao_id):
    """
    API para marcar uma notificação como lida
    """
    try:
        notificacao = get_object_or_404(Notificacao, id=notificacao_id, user=request.user)
        notificacao.marcar_como_lida()
        
        return JsonResponse({'status': 'success', 'message': 'Notificação marcada como lida'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required(login_url=URL_LOGIN)
def marcar_notificacoes_por_record_como_lidas(request, record_id):
    """
    API para marcar todas as notificações não lidas de um record como lidas
    """
    try:
        notificacoes = Notificacao.objects.filter(
            user =request.user,
            record_id=record_id,
        )
        count = notificacoes.count()
        for notificacao in notificacoes :
            notificacao.marcar_como_lida()
        
        return JsonResponse({
            'status': 'success', 
            'message': f'{count} notificação(s) marcada(s) como lida(s)',
            'count': count
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required(login_url=URL_LOGIN)
def contar_notificacoes_nao_lidas(request):
    """
    API para contar notificações não lidas do usuário logado
    """
    try:
        count = Notificacao.objects.filter(user=request.user, lida=False).count()
        return JsonResponse({'status': 'success', 'count': count})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

# Em seu arquivo views.py

@login_required(login_url='subir_ocorrencia' ) # Adapte 'URL_LOGIN' se necessário
@require_http_methods(["GET", "POST"])
def gerar_pdf_ocorrencia(request, record_id=None):
    """
    Gera um arquivo PDF com os detalhes COMPLETOS de uma ocorrência,
    com quebra de linha automática para textos longos. Versão SEM tradução.
    """
    try:
        # Se a requisição for POST, pega o ID do corpo da requisição
        if request.method == 'POST':
            data = json.loads(request.body)
            record_id = data.get('record_id')
            if not record_id:
                return JsonResponse({'status': 'error', 'message': 'ID da ocorrência não fornecido.'}, status=400)

        # Busca a ocorrência no banco de dados ou retorna um erro 404
        record = get_object_or_404(Record, id=record_id)

        # Cria um buffer de bytes em memória para o arquivo PDF
        buffer = io.BytesIO()

        # Cria o objeto PDF (canvas), usando o buffer como seu "arquivo"
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter  # Tamanho da página (8.5 x 11 polegadas)

        # --- ESTILOS PARA OS PARÁGRAFOS ---
        styles = getSampleStyleSheet()
        style_body = styles['BodyText']
        style_label = ParagraphStyle(name='Label', parent=style_body, fontName='Helvetica-Bold')

        # --- FUNÇÕES AUXILIARES INTERNAS ---
        def draw_field(x, y, label, value):
            """Desenha um par de 'Rótulo: Valor' com alinhamento dinâmico."""
            p.setFont("Helvetica-Bold", 11)
            label_text = f"{label}:"
            p.drawString(x, y, label_text)
            
            label_width = p.stringWidth(label_text, "Helvetica-Bold", 11)
            value_x_position = x + label_width + 10  # 10 pontos de espaçamento
            
            p.setFont("Helvetica", 11)
            p.drawString(value_x_position, y, str(value or "N/A"))
            
            return y - (0.25 * inch) # Retorna a próxima posição Y

        def draw_long_text_paragraph(x, y, label, text_content):
            """Desenha um rótulo e um parágrafo de texto longo com quebra de linha automática."""
            p.setFont("Helvetica-Bold", 12)
            p.drawString(x, y, f"{label}:")
            y -= 0.25 * inch

            # Prepara o texto, substituindo quebras de linha \n por   
            translated_text = traduzir_texto(text_content, target_lang='EN', api_key='71437a8a-e2de-43da-a9d7-ef10bd2550cf:fx')

            if translated_text and isinstance(translated_text, str) and translated_text.strip():
                prepared_text = translated_text.replace('\n', '<br/>')
            else:
                prepared_text = "Nenhum conteúdo fornecido."

            paragraph = Paragraph(prepared_text, style_body)
            
            available_width = width - (2 * x)
            w, h = paragraph.wrap(available_width, height)
            
            if y - h < 0.75 * inch: # Margem de segurança inferior
                p.showPage()
                y = height - 1 * inch # Reinicia no topo da nova página

            paragraph.drawOn(p, x, y - h)
            return y - h - 0.5 * inch # Retorna a posição Y final

        # ==================================================================
        # INÍCIO DO DESENHO DO CONTEÚDO DO PDF
        # ==================================================================
        
        # --- Título ---
        p.setFont("Helvetica-Bold", 18)
        p.drawCentredString(width / 2.0, height - 0.75 * inch, "Relatório de Ocorrência")
        p.setFont("Helvetica", 12)
        p.drawCentredString(width / 2.0, height - 1.0 * inch, f"ID da Ocorrência: {record.codigo_externo or record.id}")

        # --- Seção de Informações Gerais (2 colunas) ---
        y_start = height - 1.5 * inch
        p.line(0.5 * inch, y_start + 0.1 * inch, width - 0.5 * inch, y_start + 0.1 * inch)
        
        x1 = 1 * inch
        y1 = y_start - (6 * mm)
        
        y1 = draw_field(x1, y1, "Tecnhical", record.technical)
        y1 = draw_field(x1, y1, "Responsible", record.responsible)
        y1 = draw_field(x1, y1, "Country", record.country.name if record.country else None)
        y1 = draw_field(x1, y1, "Device", record.device.name if record.device else None)
        y1 = draw_field(x1, y1, "Area", record.area)

        # Coluna 2
        x2 = 4.5 * inch
        y2 = y_start - (6 * mm)

        y2 = draw_field(x2, y2, "Brand", record.brand)
        y2 = draw_field(x2, y2, "Model", record.model)
        y2 = draw_field(x2, y2, "Serial", record.serial)
        y2 = draw_field(x2, y2, "VIN", record.vin)
        y2 = draw_field(x2, y2, "Year", record.year)
        y2 = draw_field(x2, y2, "Version", record.version)

        # --- Seção de Detalhes (Textos Longos) ---
        y_next_section = min(y1, y2) - 0.3 * inch
        p.line(0.5 * inch, y_next_section + 0.1 * inch, width - 0.5 * inch, y_next_section + 0.1 * inch)
        y_text = y_next_section - 0.2 * inch
        y_text = draw_long_text_paragraph(x1, y_text, "Detected Problem", record.problem_detected) # Corrigido para "Problema Detectado"

        # ==================================================================
        # FINALIZAÇÃO DO ARQUIVO PDF
        # ==================================================================
        p.showPage()
        p.save()

        buffer.seek(0)
        filename = f'ocorrencia_{record.codigo_externo}.pdf'
        response = FileResponse(buffer, as_attachment=True, filename=filename)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Access-Control-Expose-Headers'] = 'Content-Disposition'
        
        return response

    except Record.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Ocorrência não encontrada.'}, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': 'Ocorreu um erro interno ao gerar o PDF.'}, status=500)


@login_required(login_url=URL_LOGIN)
def download_arquivo(request, arquivo_id):
    """
    View para download seguro de arquivos anexados às ocorrências
    """
    try:
        # Busca o arquivo no banco de dados
        arquivo = get_object_or_404(ArquivoOcorrencia, id=arquivo_id)
        
        # Verifica se o usuário tem permissão para acessar este arquivo
        # (baseado nas permissões de país da ocorrência)
        record = arquivo.record
        user = request.user
        
        if not user.is_superuser:
            # Verifica se o usuário tem permissão para o país da ocorrência
            if record.country:
                has_permission = CountryPermission.objects.filter(
                    user=user,
                    country=record.country
                ).exists()
                if not has_permission:
                    raise Http404("Arquivo não encontrado ou sem permissão")
        
        # Caminho completo do arquivo
        file_path = arquivo.arquivo.path
        
        # Verifica se o arquivo existe fisicamente
        if not os.path.exists(file_path):
            raise Http404("Arquivo não encontrado no sistema")
        
        # Determina o tipo MIME do arquivo
        content_type, _ = mimetypes.guess_type(file_path)
        if content_type is None:
            content_type = 'application/octet-stream'
        
        # Lê o arquivo
        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type=content_type)
        
        # Define o cabeçalho para forçar download
        filename = arquivo.nome_original or os.path.basename(file_path)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except ArquivoOcorrencia.DoesNotExist:
        raise Http404("Arquivo não encontrado")
    except Exception as e:
        # Log do erro (em produção, usar logging adequado)
        print(f"Erro no download do arquivo {arquivo_id}: {str(e)}")
        raise Http404("Erro ao processar download")
