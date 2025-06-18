# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
from datetime import datetime, date
from django.contrib.auth import authenticate, login as login_django
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from collections import defaultdict
from django.contrib import messages
from .models import Record, CountryPermission
from django.urls import reverse
import json

# Constantes para datas e status
DATE_COLUMNS = ["data", "deadline", "finished"] 
STATUS_OCORRENCIA = {
    'Concluído':'DONE',
    'Atrasado':'LATE',
    'Em progresso':'PROGRESS',
    'Requisitado':'REQUESTED'
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
    permitted_countries = CountryPermission.objects.filter(user=request.user).values_list('country', flat=True)
    context = {
        'user':request.user,
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

            base_queryset = Record.objects.all()
            user = request.user
            has_full_permission = user.is_superuser
            queryset = base_queryset

            # Limitar registros por país se não for superuser
            if not has_full_permission:
                permitted_countries = CountryPermission.objects.filter(user=user).values_list('country', flat=True)
                queryset = queryset.filter(country__in=permitted_countries)

            # Aplica filtros
            q_objects = Q()
            for column, values in filters.items():
                # Impede que usuários restritos filtrem países fora do permitido
                if column == 'country' and not has_full_permission:
                    permitted_countries = CountryPermission.objects.filter(user=user).values_list('country', flat=True)
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
                        if valid_status_keys:
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
                    else:
                        column_q |= Q(**{f'{column}__in': non_empty_values})

                if has_empty_filter:
                    column_q |= Q(**{f'{column}__isnull': True}) | Q(**{f'{column}__exact': ''})

                q_objects &= column_q

            queryset = queryset.filter(q_objects)

            # Opções de filtro
            filter_options = defaultdict(list)
            visible_columns = list(ALLOWED_SORT_COLUMNS)

            for col in FILTERABLE_COLUMNS_FOR_OPTIONS:
                if col not in visible_columns:
                    continue

                if col == 'country':
                    if has_full_permission:
                        current_col_options = base_queryset.values_list('country', flat=True).distinct()
                    else:
                        current_col_options = CountryPermission.objects.filter(user=user).values_list('country', flat=True).distinct()

                    options_list = sorted([str(opt) if opt is not None else '' for opt in current_col_options])
                    filter_options[col] = options_list
                    continue

                current_col_options = queryset.values_list(col, flat=True).distinct()
                options_list = sorted([str(opt) if opt is not None else '' for opt in current_col_options])

                if col == 'status':
                    filter_options[col] = list(set(sorted([STATUS_MAP_REVERSED.get(opt, opt) for opt in options_list if opt])))
                elif col in DATE_COLUMNS:
                    date_tree = defaultdict(lambda: defaultdict(list))
                    for dt_str in options_list:
                        if dt_str:
                            try:
                                dt = datetime.strptime(dt_str, '%Y-%m-%d').date()
                                year = str(dt.year)
                                month = dt.strftime('%m')
                                day = dt.strftime('%d')
                                if day not in date_tree[year][month]:
                                    date_tree[year][month].append(day)
                            except ValueError:
                                pass
                    for year, months in date_tree.items():
                        for month, days in months.items():
                            months[month] = sorted(days)
                        date_tree[year] = dict(sorted(months.items()))
                    filter_options[col] = dict(sorted(date_tree.items()))
                else:
                    filter_options[col] = list(set(options_list))

            # Ordenação
            sort_column = sort_info.get('column', 'data')
            sort_direction = sort_info.get('direction', 'asc')
            sort_prefix = "-" if sort_direction == 'desc' else ""

            if sort_column in ALLOWED_SORT_COLUMNS and sort_column in visible_columns:
                queryset = queryset.order_by(f"{sort_prefix}{sort_column}")
            else:
                queryset = queryset.order_by("data")

            filtered_records = list(queryset.values(*visible_columns))

            # Ajusta os registros para JSON
            for idx, record in enumerate(filtered_records):
                record['id'] = queryset[idx].id
                if 'status' in record and record['status'] in STATUS_MAP_REVERSED:
                    record['status'] = STATUS_MAP_REVERSED[record['status']]
                for date_col in DATE_COLUMNS:
                    if date_col in record:
                        if isinstance(record[date_col], (datetime, date)):
                            record[date_col] = record[date_col].strftime('%Y-%m-%d')
                        elif record[date_col] is None:
                            record[date_col] = ''

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

        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        except Exception as e:
            print(e)
            return JsonResponse({'error': 'Erro interno do servidor'}, status=500)

    return JsonResponse({'error': 'Método de requisição inválido, esperado POST'}, status=405)


def login(request):
    if request.method == "GET":
        next_url = request.GET.get('next', None)
        context = {'next': next_url} if next_url else {}
        return render(request, 'ocorrencia/login.html', context)
    else:
        name = request.POST.get('country', '').strip().capitalize()
        password = request.POST.get('password', '')
        next_url = request.POST.get('next', None)

        user = authenticate(request, username=name, password=password)

        if user is None:
            user = authenticate(request, username=name.upper(), password=password)

        if user is not None:
            login_django(request, user)
            return redirect(next_url) if next_url else redirect('/ocorrencia')
        else:
            messages.error(request, "Usuário ou senha inválidos.")
            return redirect(f"{reverse('login_ocorrencias')}?next={next_url}" if next_url else 'login_ocorrencias')


@login_required(login_url=URL_LOGIN)
def criar_usuario(request):
    if not request.user.is_superuser:
        messages.error(request, "Você precisa ser superusuário para criar um usuário.")
        return redirect('/ocorrencia')

    paises_existentes = Record.objects.values_list('country', flat=True).distinct().order_by('country')

    if request.method == "GET":
        context = {'paises': paises_existentes}
        return render(request, 'ocorrencia/criar_usuario.html', context)

    if request.method == "POST":
        username = request.POST.get('username', '').strip().upper()
        password = request.POST.get('password', '')
        paises_responsavel = request.POST.getlist('paises_responsavel')

        if not username or not password:
            messages.error(request, "Nome de usuário e senha são obrigatórios.")
            return redirect('criar_usuario')

        if User.objects.filter(username=username).exists():
            messages.warning(request, "Esse usuário já existe.")
            return redirect('criar_usuario')

        try:
            user = User.objects.create_user(username=username, password=password)
            CountryPermission.objects.filter(user=user).delete()
            for pais in paises_responsavel:
                CountryPermission.objects.create(user=user, country=pais)

            print(request, f"Usuário {username} criado com sucesso.")
            return redirect('/ocorrencia')

        except Exception as e:
            messages.error(request, f"Erro ao criar usuário: {str(e)}")
            return redirect('criar_usuario')


@login_required
def subir_ocorrencia(request):
    has_full_permission = request.user.is_superuser

    if has_full_permission:
        paises = Record.objects.values_list('country', flat=True).distinct().order_by('country')
    else:
        paises = CountryPermission.objects.filter(user=request.user).values_list('country', flat=True)

    if request.method == 'POST':
        if has_full_permission:
            country = request.POST.get("country")
        else:
            country = list(paises)[0] if paises else None

        tecnico = request.POST.get("technical")
        responsavel = request.POST.get("responsible")
        equipamento = request.POST.get("device")
        area = request.POST.get("area")
        serial = request.POST.get("serial")
        marca = request.POST.get("brand")
        modelo = request.POST.get("model")
        ano = request.POST.get("year")
        versao = request.POST.get("version")
        problema = request.POST.get("problem_detected")

        if not tecnico or not responsavel or not equipamento or not country:
            return JsonResponse({"status": "error", "message": "Campos obrigatórios não preenchidos."}, status=400)

        Record.objects.create(
            technical=tecnico,
            responsible=responsavel,
            device=equipamento,
            area=area,
            serial=serial,
            brand=marca,
            model=modelo,
            year=ano,
            country=country,
            version=versao,
            problem_detected=problema,
        )
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
            field_name = data.get('field')
            new_value = data.get('value')

            if field_name in DATE_COLUMNS and new_value:
                new_value = datetime.strptime(new_value, '%d/%m/%Y').date()

            record = Record.objects.get(id=data.get('id'))
            setattr(record, field_name, new_value)
            record.save(update_fields=[field_name])

            return JsonResponse({
                'status': 'success',
                'new_display': new_value
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error'}, status=405)
