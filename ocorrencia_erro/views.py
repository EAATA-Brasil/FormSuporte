# -*- coding: utf-8 -*-
from datetime import datetime, date
from collections import defaultdict
import os
import json
import mimetypes

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, Http404
from django.db.models import Q
from django.core.paginator import Paginator
from django.urls import reverse
from django.contrib.auth import authenticate, login as login_django, logout as logout_django
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.serializers import serialize
from django.db import IntegrityError

from .models import Record, Country, CountryPermission, Device, ArquivoOcorrencia

# Constantes
DATE_COLUMNS = ["data", "deadline", "finished"]
STATUS_OCORRENCIA = {
    'Concluído': 'DONE',
    'Atrasado': 'LATE',
    'Em progresso': 'PROGRESS',
    'Requisitado': 'REQUESTED'
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

def get_responsaveis():
    paises = Country.objects.all().order_by('name')
    responsaveis_por_pais = {}
    todos_responsaveis = []
    
    # Buscar todos os usuários que têm permissões de país (são responsáveis)
    usuarios_com_permissao = User.objects.filter(
        country_permissions__isnull=False
    ).distinct().values('id', 'first_name', 'last_name', 'username')
    

    # Criar lista de todos os responsáveis
    responsaveis_dict = {}
    for user in usuarios_com_permissao:
        nome_completo = f"{user['first_name']} {user['last_name']}".strip()
        if not nome_completo:
            nome_completo = user['username']
        
        responsavel_data = {
            'id': user['id'],
            'name': nome_completo
        }
        
        todos_responsaveis.append(responsavel_data)
        responsaveis_dict[user['id']] = responsavel_data
            
    # Mapear responsáveis por país usando CountryPermission
    for pais in paises:
        # Buscar usuários que têm permissão neste país
        permissoes = CountryPermission.objects.filter(country=pais).select_related('user')
        
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
    return(responsaveis_por_pais_json, todos_responsaveis_json)

def subir_arquivo(files, record):
    for file in files:
        print(file)
        # Extrai a extensão do arquivo original
        ext = os.path.splitext(file.name)[1]  # inclui o ponto, ex: ".jpg"

        # Define o novo nome do arquivo
        novo_nome = f"image_relatorio_{record.id}{ext}"

        # Opcional: definir o nome dentro do arquivo UploadedFile (não obrigatório para salvar)
        file.name = novo_nome

        # Cria o registro no banco
        ArquivoOcorrencia.objects.create(
            record=record,
            arquivo=file,
            nome_original=novo_nome  # ou mantenha file.name se preferir
        )


@login_required(login_url=URL_LOGIN)
def index(request):
    responsaveis_por_pais_json, todos_responsaveis_json = get_responsaveis()
    
    responsaveis = json.loads(todos_responsaveis_json)

    # 2. Mapeia status técnicos para nomes legíveis
    status_map = {
        Record.STATUS_OCORRENCIA.DONE: "Concluído",
        Record.STATUS_OCORRENCIA.LATE: "Atrasado",
        Record.STATUS_OCORRENCIA.PROGRESS: "Em progresso",
        Record.STATUS_OCORRENCIA.REQUESTED: "Requisitado"
    }

    # 3. Inicializa dicionário de contagem
    ocorrencias_dict = {}

    for responsavel in responsaveis:
        nome = responsavel.get('name') or responsavel.get('nome') or responsavel.get('responsible')
        if nome:
            ocorrencias_dict[nome] = {label: 0 for label in status_map.values()}

    # 4. Consulta todos os registros e agrupa por responsável e status
    for record in Record.objects.all().values('responsible', 'status'):
        nome = record['responsible']
        status_codigo = record['status']
        status_legivel = status_map.get(status_codigo)

        if nome in ocorrencias_dict and status_legivel:
            ocorrencias_dict[nome][status_legivel] += 1

    # 5. Resultado final
    ocorrencias_json = json.dumps(ocorrencias_dict, ensure_ascii=False)

    is_super = request.user.is_superuser
    permitted_countries = Country.objects.filter(
        countrypermission__user=request.user
    ).values_list('name', flat=True)

    context = {
        'user': request.user,
        'paises_permitidos': permitted_countries,
        'has_full_permission': is_super,
        'responsaveis_por_pais': responsaveis_por_pais_json,
        'todos_responsaveis': todos_responsaveis_json,
        'ocorrencias_json':ocorrencias_json,
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

            # Consulta base otimizada
            base_queryset = Record.objects.select_related('country').all()
            user = request.user
            has_full_permission = user.is_superuser

            queryset = base_queryset
            # Construção dos filtros
            q_objects = Q()
            for column, values in filters.items():
                if not isinstance(values, list) or not values:
                    continue

                column_q = Q()
                has_empty = '' in values
                non_empty = [v for v in values if v != '']

                TEXT_CASE_INSENSITIVE_COLUMNS = [
                    'codigo_externo', 'technical', 'area', 'serial', 'brand', 'model',
                    'version', 'responsible', 'problem_detected', 'feedback_technical',
                    'feedback_manager'
                ]

                # Filtros para valores não vazios
                if non_empty:
                    if column == 'status':
                        status_values = [STATUS_OCORRENCIA.get(v, v) for v in non_empty]
                        column_q |= Q(status__in=status_values)
                    elif column in DATE_COLUMNS:
                        dates = []
                        for v in non_empty:
                            try:
                                if '/' in v:  # Formato DD/MM/YYYY
                                    dt = datetime.strptime(v, '%d/%m/%Y').date()
                                else:  # Formato YYYY-MM-DD
                                    dt = datetime.strptime(v, '%Y-%m-%d').date()
                                dates.append(dt)
                            except:
                                continue
                        if dates:
                            column_q |= Q(**{f'{column}__in': dates})
                    elif column == 'country':
                        if has_full_permission:
                            country_q_objects = Q()
                            for val in non_empty:
                                country_q_objects |= Q(country__name__iexact=val)
                            column_q |= country_q_objects
                        else:
                            permitted = set(CountryPermission.objects.filter(
                                user=user,
                                country__name__in=non_empty
                            ).values_list('country__name', flat=True))
                            filtered = [v for v in non_empty if v in permitted]
                            if filtered:
                                country_q_objects = Q()
                                for val in filtered:
                                    country_q_objects |= Q(country__name__iexact=val)
                                column_q |= country_q_objects
                    elif column == 'device':
                        if has_full_permission:
                            device_q_objects = Q()
                            for val in non_empty:
                                device_q_objects |= Q(device__name__iexact=val)
                            column_q |= device_q_objects
                    elif column in TEXT_CASE_INSENSITIVE_COLUMNS:
                        text_q_objects = Q()
                        for val in non_empty:
                            text_q_objects |= Q(**{f'{column}__iexact': val})
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

            # Ordenação (mantida igual)
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

            # Paginação
            paginator = Paginator(queryset, 11)
            page_obj = paginator.get_page(page_number)

            # Prepara os dados para resposta
            records_data = []
            for record in page_obj.object_list:
                record_data = {
                    'id':record.id,
                    'codigo_externo': record.codigo_externo or str(record.id),  # Usar codigo_externo ou id como fallback
                    'data': record.data or '',
                    'technical': record.technical or '',
                    'country': record.country.name if record.country else '',
                    'device': record.device.name if record.device else '',
                    'area': record.area or '',
                    'serial': record.serial or '',
                    'brand': record.brand or '',
                    'model': record.model or '',
                    'year': record.year or '',
                    'version': record.version or '',
                    'problem_detected': record.problem_detected or '',
                    'status': STATUS_MAP_REVERSED.get(record.status, record.status or ''),
                    'deadline': record.deadline.strftime('%d/%m/%Y') if record.deadline else '',
                    'responsible': record.responsible or '',
                    'finished': record.finished.strftime('%d/%m/%Y') if record.finished else '',
                    'feedback_technical': record.feedback_technical or '',
                    'feedback_manager': record.feedback_manager or '',
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
                records_data.append(record_data)

            # Atualizar FILTERABLE_COLUMNS_FOR_OPTIONS para incluir codigo_externo
            FILTERABLE_COLUMNS_FOR_OPTIONS = [
                'codigo_externo', 'technical', 'country', 'device', 'area', 'serial', 'brand',
                'model', 'year', 'version', 'status', 'responsible',
                'data', 'deadline', 'finished'
            ]

            filter_options = {}
            for col in FILTERABLE_COLUMNS_FOR_OPTIONS:
                if col == 'country':
                    if has_full_permission:
                        options = base_queryset.exclude(country__isnull=True
                                ).values_list('country__name', flat=True).distinct()
                    else:
                        options = CountryPermission.objects.filter(
                            user=user
                        ).values_list('country__name', flat=True).distinct()
                    filter_options[col] = sorted(list(set([opt.upper() for opt in options if opt])))
                elif col == 'device':
                    if has_full_permission:
                        options = base_queryset.exclude(device__isnull=True
                                ).values_list('device__name', flat=True).distinct()
                    filter_options[col] = sorted(list(set([opt.upper() for opt in options if opt])))
                elif col == 'status':
                    status_values = queryset.values_list('status', flat=True).distinct()
                    filter_options[col] = sorted(
                        [STATUS_MAP_REVERSED.get(opt, opt) for opt in status_values if opt],
                        key=lambda x: list(STATUS_OCORRENCIA.keys()).index(x) if x in STATUS_OCORRENCIA else float('inf')
                    )
                elif col in DATE_COLUMNS:
                    dates = queryset.exclude(**{f'{col}__isnull': True}
                            ).values_list(col, flat=True).distinct()
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
                    options = queryset.exclude(**{f'{col}__isnull': True}
                            ).exclude(**{f'{col}__exact': ''}
                            ).values_list(col, flat=True).distinct()
                    filter_options[col] = sorted(list(set([opt.upper() for opt in options if opt is not None])))

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
        paises_responsavel = request.POST.getlist('paises_responsavel')

        if not username or not password:
            messages.error(request, "Nome de usuário e senha obrigatórios.")
            return redirect('criar_usuario')

        if User.objects.filter(username=username).exists():
            messages.warning(request, "Usuário já existe.")
            return redirect('criar_usuario')

        user = User.objects.create_user(username=username, password=password)
        for pais_id in paises_responsavel:
            try:
                country = Country.objects.get(id=pais_id)
                CountryPermission.objects.create(user=user, country=country)
            except Country.DoesNotExist:
                continue

        messages.success(request, f"Usuário {username} criado com sucesso.")
        return redirect('criar_usuario')



# @login_required(login_url='subir_ocorrencia')
def subir_ocorrencia(request):
    has_full_permission = request.user.is_superuser
    paises = Country.objects.all().order_by('name')
    responsaveis_por_pais = {}
    todos_responsaveis = []
    todos_equipamentos = []

    # Prepara lista de responsáveis
    usuarios_com_permissao = User.objects.filter(
        country_permissions__isnull=False
    ).distinct().values('id', 'first_name', 'last_name', 'username')

    for user in usuarios_com_permissao:
        nome_completo = f"{user['first_name']} {user['last_name']}".strip()
        if not nome_completo:
            nome_completo = user['username']
        todos_responsaveis.append({'id': user['id'], 'name': nome_completo})

    # Prepara lista de equipamentos
    todos_equipamentos = list(Device.objects.all().values('id', 'name'))

    # Mapeia responsáveis por país
    for pais in paises:
        responsaveis_por_pais[pais.id] = []
        for permissao in CountryPermission.objects.filter(country=pais).select_related('user'):
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
                'brand': request.POST.get("brand"),
                'model': request.POST.get("model"),
                'year': request.POST.get("year"),
                'country': country,
                'version': request.POST.get("version"),
                'problem_detected': request.POST.get("problem_detected"),
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
            try:
                record = Record.objects.create(**record_data)
            except IntegrityError as e:
                return JsonResponse({
                    "status": "error",
                    "message": "Erro ao criar registro. Verifique os dados."
                }, status=400)

            # Processa arquivos anexados
            for file in request.FILES.getlist("arquivo"):
                ext = os.path.splitext(file.name)[1]
                novo_nome = f"ocorrencia_{record.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}{ext}"
                ArquivoOcorrencia.objects.create(
                    record=record,
                    arquivo=file,
                    nome_original=novo_nome
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
    return render(request, 'ocorrencia/subir_ocorrencia.html', {
        'paises': paises,
        'paises_json': json.dumps(paises_dict),
        'has_full_permission': has_full_permission,
        'responsaveis_por_pais': json.dumps(responsaveis_por_pais),
        'todos_responsaveis': json.dumps(todos_responsaveis),
        'todos_equipamentos_raw': todos_equipamentos,
    })
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

@login_required(login_url=URL_LOGIN)
def alterar_dados(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=405)

    try:
        if request.content_type.startswith('multipart/form-data'):
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
                        ext = os.path.splitext(file.name)[1]
                        novo_nome = f"image_relatorio_{record}{ext}"
                        file.name = novo_nome
                        ArquivoOcorrencia.objects.create(
                            record=record,
                            arquivo=file,
                            nome_original=novo_nome
                        )
                    return JsonResponse({'status': 'success', 'page_num': body.get("page_num")})
                except Exception as e:
                    return JsonResponse({'status': 'error','message': f'Erro ao salvar arquivos: {str(e)}'}, status=500)

        else:
            # JSON puro (sem arquivos)
            data = json.loads(request.body.decode('utf-8'))
            record = Record.objects.get(id=data.get('id'))
            field_name = data.get('field')
            new_value = data.get('value')

            if field_name == 'country':
                new_value = get_object_or_404(Country, id=new_value)
                setattr(record, field_name, new_value)
                new_display = new_value.name

            elif field_name in DATE_COLUMNS and new_value:
                new_value = datetime.strptime(new_value, '%d/%m/%Y').date()
                setattr(record, field_name, new_value)
                new_display = new_value.strftime('%Y-%m-%d')

            elif field_name == 'status':
                if record.finished:
                    new_value = 'Concluído'
                elif record.deadline:
                    if record.deadline < date.today():
                        new_value = 'Atrasado'
                    else:
                        new_value = "Em progresso"
                else:
                    new_value = 'Requisitado'

                new_display = new_value
                new_value = STATUS_OCORRENCIA.get(new_value)
                setattr(record, field_name, new_value)

            else:
                setattr(record, field_name, new_value.capitalize())
                new_display = new_value.capitalize()

            record.save(update_fields=[field_name])
            return JsonResponse({'status': 'success', 'new_display': new_display, 'page_num': data.get("page_num")})

    except Exception as e:
        print(e)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

# Alias para compatibilidade com URLs existentes
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
            "brand": record.brand,
            "model": record.model,
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
