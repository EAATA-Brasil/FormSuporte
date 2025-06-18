# -*- coding: utf-8 -*-
from datetime import datetime, date
from collections import defaultdict
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
from django.urls import reverse
from django.contrib.auth import authenticate, login as login_django
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Record, Country, CountryPermission

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

URL_LOGIN = 'login_ocorrencias'

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
            data = json.loads(request.body)
            filters = data.get('filters', {})
            sort_info = data.get('sort', {'column': 'data', 'direction': 'asc'})

            base_queryset = Record.objects.select_related('country').all()
            user = request.user
            has_full_permission = user.is_superuser
            queryset = base_queryset

            # Restrição por país
            if not has_full_permission:
                permitted_countries = CountryPermission.objects.filter(user=user).values_list('country', flat=True)
                queryset = queryset.filter(country__in=permitted_countries)

            # Aplicar filtros
            q_objects = Q()
            for column, values in filters.items():
                if column == 'country' and not has_full_permission:
                    permitted_countries = Country.objects.filter(
                        countrypermission__user=user
                    ).values_list('name', flat=True)
                    values = [v for v in values if v in permitted_countries]
                    if not values:
                        continue

                if not isinstance(values, list) or not values:
                    continue

                column_q = Q()
                has_empty_filter = '' in values
                non_empty_values = [v for v in values if v != '']

                if non_empty_values:
                    if column == 'status':
                        valid_status_keys = [STATUS_OCORRENCIA[v] for v in non_empty_values if v in STATUS_OCORRENCIA]
                        column_q |= Q(**{f'{column}__in': valid_status_keys})
                    elif column in DATE_COLUMNS:
                        valid_dates = []
                        for v in non_empty_values:
                            try:
                                datetime.strptime(v, '%Y-%m-%d')
                                valid_dates.append(v)
                            except ValueError:
                                pass
                        if valid_dates:
                            column_q |= Q(**{f'{column}__in': valid_dates})
                    elif column == 'country':
                        column_q |= Q(country__name__in=non_empty_values)
                    else:
                        column_q |= Q(**{f'{column}__in': non_empty_values})

                if has_empty_filter:
                    if column == 'country':
                        column_q |= Q(country__isnull=True)
                    else:
                        column_q |= Q(**{f'{column}__isnull': True}) | Q(**{f'{column}__exact': ''})

                q_objects &= column_q

            queryset = queryset.filter(q_objects)

            # Preparar opções de filtro
            filter_options = defaultdict(list)
            visible_columns = list(ALLOWED_SORT_COLUMNS)

            for col in FILTERABLE_COLUMNS_FOR_OPTIONS:
                if col == 'country':
                    if has_full_permission:
                        current_col_options = base_queryset.values_list('country__name', flat=True).distinct()
                    else:
                        current_col_options = CountryPermission.objects.filter(
                            user=user
                        ).values_list('country__name', flat=True).distinct()
                    filter_options[col] = sorted([opt or '' for opt in current_col_options])
                elif col == 'status':
                    status_values = queryset.values_list('status', flat=True).distinct()
                    filter_options[col] = sorted([STATUS_MAP_REVERSED.get(opt, opt) for opt in status_values if opt])
                elif col in DATE_COLUMNS:
                    dates = queryset.values_list(col, flat=True).distinct()
                    date_tree = defaultdict(lambda: defaultdict(list))
                    for dt in dates:
                        if dt:
                            try:
                                dt = datetime.strptime(str(dt), '%Y-%m-%d').date()
                                year = str(dt.year)
                                month = dt.strftime('%m')
                                day = dt.strftime('%d')
                                if day not in date_tree[year][month]:
                                    date_tree[year][month].append(day)
                            except:
                                pass
                    for year in date_tree:
                        for month in date_tree[year]:
                            date_tree[year][month] = sorted(date_tree[year][month])
                        date_tree[year] = dict(sorted(date_tree[year].items()))
                    filter_options[col] = dict(sorted(date_tree.items()))
                else:
                    options = queryset.values_list(col, flat=True).distinct()
                    filter_options[col] = sorted([opt or '' for opt in options])

            # Ordenação
            sort_column = sort_info.get('column', 'data')
            sort_direction = sort_info.get('direction', 'asc')
            sort_prefix = "-" if sort_direction == 'desc' else ""

            if sort_column in ALLOWED_SORT_COLUMNS:
                if sort_column == 'country':
                    queryset = queryset.order_by(f"{sort_prefix}country__name")
                else:
                    queryset = queryset.order_by(f"{sort_prefix}{sort_column}")

            filtered_records = list(queryset.values(*visible_columns, 'country__name'))

            # Substituir id por nome do país
            for idx, record in enumerate(filtered_records):
                record['id'] = queryset[idx].id
                if 'status' in record and record['status'] in STATUS_MAP_REVERSED:
                    record['status'] = STATUS_MAP_REVERSED[record['status']]
                for date_col in DATE_COLUMNS:
                    if date_col in record and record[date_col]:
                        record[date_col] = str(record[date_col])
                if 'country' in record or 'country__name' in record:
                    record['country'] = record.pop('country__name', '')

            paginator = Paginator(filtered_records, 10)
            page_number = data.get('page')
            page_obj = paginator.get_page(page_number)

            return JsonResponse({
                'records': list(page_obj.object_list),
                'filter_options': filter_options,
                'has_full_permission': has_full_permission,
                'num_pages': paginator.num_pages,
                'current_page': page_obj.number,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            })

        except Exception as e:
            print(e)
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método inválido'}, status=405)


def login(request):
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


@login_required(login_url=URL_LOGIN)
def subir_ocorrencia(request):
    has_full_permission = request.user.is_superuser

    if has_full_permission:
        paises = Country.objects.all().order_by('name')
    else:
        paises = Country.objects.filter(
            id__in=CountryPermission.objects.filter(user=request.user).values_list('country_id', flat=True)
        ).order_by('name')
    if request.method == 'POST':
        country_id = request.POST.get("country")
        country = get_object_or_404(Country, id=country_id) if has_full_permission else paises.first()
        record_data = {
            'technical': request.POST.get("technical"),
            'responsible': request.POST.get("responsible"),
            'device': request.POST.get("device"),
            'area': request.POST.get("area"),
            'serial': request.POST.get("serial"),
            'brand': request.POST.get("brand"),
            'model': request.POST.get("model"),
            'year': request.POST.get("year"),
            'country': country,
            'version': request.POST.get("version"),
            'problem_detected': request.POST.get("problem_detected"),
            'status': STATUS_OCORRENCIA.get(f'{request.POST.get("status", "Requisitado")}','REQUESTED')
        }

        # Adiciona 'deadline' apenas se existir no POST e não for vazio
        if request.POST.get("deadline"):
            record_data['deadline'] = request.POST.get("deadline")

        # Cria o registro
        Record.objects.create(**record_data)
        return JsonResponse({"status": "success", "message": "Ocorrência cadastrada com sucesso."}, status=201)

    return render(request, 'ocorrencia/subir_ocorrencia.html', {
        'paises': paises,
        'has_full_permission': has_full_permission,
    })


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
            else:
                setattr(record, field_name, new_value)
                new_display = new_value

            record.save(update_fields=[field_name])

            return JsonResponse({'status': 'success', 'new_display': new_display})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error'}, status=405)
