# -*- coding: utf-8 -*-
from datetime import datetime, date
from collections import defaultdict
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
from django.urls import reverse
from django.contrib.auth import authenticate, login as login_django, logout as logout_django
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Record, Country, CountryPermission, Device

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
    'technical', 'country', 'device', 'area', 'serial', 'brand',
    'model', 'year', 'version', 'status', 'responsible',
    'data', 'deadline', 'finished'
]

URL_LOGIN = 'subir_ocorrencia'

@login_required(login_url=URL_LOGIN)
def index(request):
    is_super = request.user.is_superuser
    permitted_countries = Country.objects.filter(
        countrypermission__user=request.user
    ).values_list('name', flat=True)

    context = {
        'user': request.user,
        'paises_permitidos': permitted_countries,
        'has_full_permission': is_super
    }
    return render(request, 'ocorrencia/index.html', context)


@login_required(login_url=URL_LOGIN)
def filter_data_view(request):
    if request.method == 'POST':
        try:
            # print("Raw request data:", request.body)  # Debug
            data = json.loads(request.body)
            # print("Parsed JSON data:", data)
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
                    'technical', 'area', 'serial', 'brand', 'model',
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
                        # Para país, a busca é por nome, que pode ser case-insensitive
                        # Mas como você já tem um filtro de permissão, vamos manter a lógica de permissão
                        # e adicionar a case-insensitivity na busca pelo nome do país.
                        if has_full_permission:
                            # Usar __iexact para correspondência exata case-insensitive
                            country_q_objects = Q()
                            for val in non_empty:
                                country_q_objects |= Q(country__name__iexact=val)
                            column_q |= country_q_objects
                        else:
                            permitted = set(CountryPermission.objects.filter(
                                user=user,
                                country__name__in=non_empty # Isso aqui já pode ser um problema se o nome no DB for diferente da permissão
                            ).values_list('country__name', flat=True))
                            filtered = [v for v in non_empty if v in permitted]
                            if filtered:
                                # Usar __iexact para correspondência exata case-insensitive
                                country_q_objects = Q()
                                for val in filtered:
                                    country_q_objects |= Q(country__name__iexact=val)
                                column_q |= country_q_objects
                    elif column == 'device':
                        # Para país, a busca é por nome, que pode ser case-insensitive
                        # Mas como você já tem um filtro de permissão, vamos manter a lógica de permissão
                        # e adicionar a case-insensitivity na busca pelo nome do país.
                        if has_full_permission:
                            # Usar __iexact para correspondência exata case-insensitive
                            device_q_objects = Q()
                            for val in non_empty:
                                device_q_objects |= Q(device__name__iexact=val)
                            column_q |= device_q_objects

                    elif column in TEXT_CASE_INSENSITIVE_COLUMNS:
                        # Para colunas de texto, usar __iexact para correspondência exata case-insensitive
                        # Ou __icontains se você quiser uma busca "contém" case-insensitive
                        text_q_objects = Q()
                        for val in non_empty:
                            text_q_objects |= Q(**{f'{column}__iexact': val}) # Use __iexact para correspondência exata
                            # Se preferir "contém", use: text_q_objects |= Q(**{f'{column}__icontains': val})
                        column_q |= text_q_objects
                    else:
                        # Para outras colunas, mantém o filtro padrão (case-sensitive)
                        column_q |= Q(**{f'{column}__in': non_empty})

                # Filtro para valores vazios/nulos
                if has_empty:
                    if column == 'country':
                        column_q |= Q(country__isnull=True)
                    elif column == 'device':
                        column_q |= Q(device__isnull=True)
                    else:
                        column_q |= Q(**{f'{column}__isnull': True}) | Q(**{f'{column}__exact': ''})

                if column_q:
                    q_objects &= column_q

            # Aplica os filtros se houver algum
            if q_objects:
                queryset = queryset.filter(q_objects)

            # Ordenação
            sort_column = sort_info.get('column', 'data')
            sort_direction = sort_info.get('direction', 'asc')
            
            if sort_column in ALLOWED_SORT_COLUMNS:
                if sort_column == 'country':
                    # Para ordenação de país, use country__name
                    order_field = f"{'-' if sort_direction == 'desc' else ''}country__name"
                if sort_column == 'device':
                    # Para ordenação de país, use country__name
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
                    'id': record.id,
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
                }
                records_data.append(record_data)

            # Prepara opções de filtro para a resposta
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
                    # Padroniza para maiúsculas para unicidade na lista de opções
                    filter_options[col] = sorted(list(set([opt.upper() for opt in options if opt])))
                elif col == 'device':
                    if has_full_permission:
                        options = base_queryset.exclude(device__isnull=True
                                ).values_list('device__name', flat=True).distinct()
                    # Padroniza para maiúsculas para unicidade na lista de opções
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
        username = request.POST.get('username', '').strip().upper()
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
        return redirect('/ocorrencia')


def subir_ocorrencia(request):
    has_full_permission = request.user.is_superuser
    paises = Country.objects.all().order_by('name')
    
    # Buscar responsáveis baseado no modelo CountryPermission
    # Criar mapeamento de responsáveis por país
    responsaveis_por_pais = {}
    todos_responsaveis = []
    todos_equipamentos = []
    
    # Buscar todos os usuários que têm permissões de país (são responsáveis)
    usuarios_com_permissao = User.objects.filter(
        country_permissions__isnull=False
    ).distinct().values('id', 'first_name', 'last_name', 'username')
    
    equipamentos_possiveis = Device.objects.all().values('id','name')

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

    equipamento_dict = {}
    for equipamento in equipamentos_possiveis:
        equipamento_data ={
            'id': equipamento['id'],
            'name': equipamento['name']
        }
        todos_equipamentos.append(equipamento_data)
        equipamento_dict[equipamento['id']]=equipamento_data
            
    # Mapear responsáveis por país usando CountryPermission
    for pais in paises:
        # Buscar usuários que têm permissão neste país
        permissoes = CountryPermission.objects.filter(country=pais).select_related('user')
        
        responsaveis_por_pais[pais.id] = []
        for permissao in permissoes:
            user = permissao.user
            nome_completo = f"{user.first_name} {user.last_name}".strip()
            if not nome_completo:
                nome_completo = user.username
            
            responsaveis_por_pais[pais.id].append({
                'id': user.id,
                'name': nome_completo
            })
    
    if request.method == 'POST':
        country_id = request.POST.get("country")
        country = get_object_or_404(Country, id=country_id) if has_full_permission else paises.first()
        device_id = request.POST.get("device")
        device = get_object_or_404(Device, id=device_id) 


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
            'status': Record.STATUS_OCORRENCIA.REQUESTED  # Usando o enum correto
        }

        # Processar status se fornecido
        status_mapping = {
            'Requisitado': Record.STATUS_OCORRENCIA.REQUESTED,
            'Concluído': Record.STATUS_OCORRENCIA.DONE,
            'Em progresso': Record.STATUS_OCORRENCIA.PROGRESS,
            'Atrasado': Record.STATUS_OCORRENCIA.LATE,
        }
        
        status_input = request.POST.get("status", "Requisitado")
        if status_input in status_mapping:
            record_data['status'] = status_mapping[status_input]

        # Adiciona 'deadline' apenas se existir no POST e não for vazio
        if request.POST.get("deadline"):
            try:
                record_data['deadline'] = datetime.strptime(request.POST.get("deadline"), '%d/%m/%Y').date()
            except Exception as e:
                print(e)
                record_data['deadline'] = request.POST.get("deadline")

        # Cria o registro
        Record.objects.create(**record_data)
        return JsonResponse({"status": "success", "message": "Ocorrência cadastrada com sucesso."}, status=201)

    # Converter para JSON para uso no template
    responsaveis_por_pais_json = json.dumps(responsaveis_por_pais)
    todos_responsaveis_json = json.dumps(todos_responsaveis)
    todos_equipamentos_json = json.dumps(todos_equipamentos)

    return render(request, 'ocorrencia/subir_ocorrencia.html', {
        'paises': paises,
        'has_full_permission': has_full_permission,
        'responsaveis_por_pais': responsaveis_por_pais_json,
        'todos_responsaveis': todos_responsaveis_json,
        'responsaveis_por_pais_raw': responsaveis_por_pais,  # Para debug se necessário
        'todos_responsaveis_raw': todos_responsaveis,  # Para debug se necessário
        'todos_equipamentos_raw': todos_equipamentos,  # Para debug se necessário
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
    if request.method == 'POST':
        try:
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
                if record.deadline:
                    if record.finished:
                        new_value = 'Concluído'
                    else:
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
                setattr(record, field_name, new_value)
                new_display = new_value
            
            record.save(update_fields=[field_name])
            return JsonResponse({'status': 'success', 'new_display': new_display, 'page_num': data.get("page_num")})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error'}, status=405)
