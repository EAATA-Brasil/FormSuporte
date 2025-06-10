# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db.models import Q, Count
import json
from .models import Record # Certifique-se que o modelo Record está importado corretamente
from datetime import datetime, date
from django.http import HttpResponse
from django.contrib.auth import authenticate, login as login_django
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from collections import defaultdict
from django.contrib import messages
from django.urls import reverse

# Defina as colunas que são do tipo data (devem corresponder ao JS)
DATE_COLUMNS = ["data", "deadline", "finished"] 
STATUS_OCORRENCIA = {
    # Mapeamento de status legível para status armazenado
    'Concluído':'DONE',
    'Atrasado':'LATE',
    'Em progresso':'PROGRESS',
    'Requisitado':'REQUESTED'
}
STATUS_MAP_REVERSED = {v: k for k, v in STATUS_OCORRENCIA.items()}

# Defina todas as colunas que podem ser ordenadas e filtradas
ALLOWED_SORT_COLUMNS = [
    'feedback_manager', 'feedback_technical', 'problem_detected', 'area', 'brand', 
    'country', 'data', 'deadline', 'device', 'finished', 'model', 'responsible', 
    'serial', 'status', 'technical', 'version', 'year'
] 

# Colunas para as quais queremos gerar opções de filtro dinâmicas
FILTERABLE_COLUMNS_FOR_OPTIONS = [
    'technical', 'country', 'device', 'area', 'serial', 'brand', 
    'model', 'year', 'version', 'status', 'responsible', 
    'data', 'deadline', 'finished' # Incluindo datas
]

URL_LOGIN = 'login_ocorrencias'

# View principal
@login_required(login_url=URL_LOGIN)
def index(request):
    is_super = request.user.is_superuser
    #print(f"--- View Index --- Usuário: {request.user.username}, É Superusuário? {is_super}") # DEBUG
    context = {
        'has_full_permission': is_super
    }
    return render(request, 'ocorrencia/index.html', context)

# View para filtrar e ordenar dados via AJAX
@login_required(login_url=URL_LOGIN)
def filter_data_view(request):
    #print("\n--- filter_data_view INICIADA ---")
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            filters = data.get('filters', {})
            sort_info = data.get('sort', {'column': 'data', 'direction': 'asc'})
            print(f"Filtros recebidos: {filters}")
            #print(f"Ordenação recebida: {sort_info}")

            # Comece com todos os registros
            base_queryset = Record.objects.all()
            #print(f"Contagem inicial do queryset: {base_queryset.count()}")
            
            # --- LÓGICA DE PERMISSÃO ---
            user = request.user
            has_full_permission = user.is_superuser 
            queryset = base_queryset

            if not has_full_permission:
                #print(f"Usuário restrito detectado: {user.username}. Filtrando por país.")
                queryset = queryset.filter(country__iexact=user.username) 
                #print(f"Contagem após filtro de país: {queryset.count()}")
            else:
                print("Usuário com permissão total detectado.")
            
            # --- APLICA FILTROS DO FRONTEND --- 
            q_objects = Q()
            #print("Processando filtros do frontend...")
            for column, values in filters.items():
                #print(f"  Processando filtro para coluna: {column}, valores: {values}")
                if column == 'country' and not has_full_permission:
                    #print("    Ignorando filtro de país do frontend para usuário restrito.")
                    continue

                if not isinstance(values, list):
                    #print(f"    Ignorando filtro inválido (não é lista) para {column}: {values}")
                    continue
                
                if not values:
                    #print(f"    Filtro vazio para {column}, ignorando.")
                    continue 

                column_q = Q()
                # Trata valores vazios ("") como nulos ou strings vazias
                has_empty_filter = '' in values 
                non_empty_values = [v for v in values if v != '']
                #print(f"    Valores não vazios: {non_empty_values}, Filtro vazio presente: {has_empty_filter}")
                
                if non_empty_values:
                    if column == 'status':
                        valid_status_keys = []
                        for v in non_empty_values:
                            # Compara com os valores legíveis (chaves do dicionário)
                            if v in STATUS_OCORRENCIA:
                                valid_status_keys.append(STATUS_OCORRENCIA[v])
                        if valid_status_keys:
                            column_q |= Q(**{f'{column}__in': valid_status_keys})
                            #print(f"      Adicionando Q para status: {column_q}")
                    elif column in DATE_COLUMNS:
                        # Para datas, o frontend envia YYYY-MM-DD
                        valid_dates = []
                        for v in non_empty_values:
                            try:
                                # Apenas valida o formato, a query usa o string
                                datetime.strptime(v, '%Y-%m-%d') 
                                valid_dates.append(v)
                            except ValueError:
                                print(f"      Ignorando formato de data inválido para {column}: {v}")
                        if valid_dates:
                            column_q |= Q(**{f'{column}__in': valid_dates})
                            #print(f"      Adicionando Q para data: {column_q}")
                    else:
                        # Para outras colunas, usa __in diretamente
                        column_q |= Q(**{f'{column}__in': non_empty_values})
                        #print(f"      Adicionando Q para coluna normal: {column_q}")

                if has_empty_filter:
                    # Filtra por nulo OU string vazia
                    column_q |= Q(**{f'{column}__isnull': True}) | Q(**{f'{column}__exact': ''})
                    #print(f"      Adicionando Q para filtro vazio: {column_q}")
                
                if column_q: # Só adiciona ao q_objects se alguma condição foi gerada
                    #print(f"    Combinando Q para {column}: {column_q}")
                    q_objects &= column_q
                    #print(f"    q_objects atual: {q_objects}")
                else:
                    print(f"    Nenhuma condição Q gerada para {column}.")

            #print(f"\nObjeto Q final combinado: {q_objects}")
            # Aplica o filtro combinado ao queryset
            queryset = queryset.filter(q_objects)
            #print(f"Contagem após aplicar filtros do frontend: {queryset.count()}")

            # --- CALCULA OPÇÕES DE FILTRO DISPONÍVEIS --- 
            # Fazemos isso *depois* de aplicar os filtros, para que as opções sejam relevantes
            filter_options = defaultdict(list)
            #print("\nCalculando opções de filtro disponíveis...")
            # Determina colunas visíveis para o usuário atual
            visible_columns = list(ALLOWED_SORT_COLUMNS)
            if not has_full_permission and 'country' in visible_columns:
                visible_columns.remove('country')
            
            # Itera apenas sobre colunas que podem ter filtros e são visíveis
            for col in FILTERABLE_COLUMNS_FOR_OPTIONS:
                if col not in visible_columns:
                    continue # Pula colunas não visíveis (como 'country' para não superuser)
                
                #print(f"  Calculando opções para: {col}")
                # Otimização: Usar values_list e distinct
                # Trata valores nulos como strings vazias para consistência com o filtro
                current_col_options = queryset.values_list(col, flat=True).distinct()
                # Converte para string e trata None como ''
                options_list = sorted([str(opt) if opt is not None else '' for opt in current_col_options])

                # Formatação especial para status e datas
                if col == 'status':
                    # Mapeia de volta para os nomes legíveis
                    filter_options[col] = list(set(sorted([STATUS_MAP_REVERSED.get(opt, opt) for opt in options_list if opt]))) # Ignora vazio aqui?
                elif col in DATE_COLUMNS:
                    # Agrupa datas por ano/mês/dia para a árvore
                    date_tree = defaultdict(lambda: defaultdict(list))
                    for dt_str in options_list:
                        if dt_str: # Ignora datas vazias/nulas
                            try:
                                dt = datetime.strptime(dt_str, '%Y-%m-%d').date()
                                year = str(dt.year)
                                month = dt.strftime('%m') # Formato MM
                                day = dt.strftime('%d') # Formato DD
                                if day not in date_tree[year][month]:
                                     date_tree[year][month].append(day)
                            except ValueError:
                                print(f"Data inválida encontrada ao gerar opções para {col}: {dt_str}")
                    # Ordena meses e dias
                    for year, months in date_tree.items():
                        for month, days in months.items():
                            months[month] = sorted(days)
                        date_tree[year] = dict(sorted(months.items()))
                    filter_options[col] = dict(sorted(date_tree.items())) # Envia a árvore
                else:
                    filter_options[col] = list(set(options_list))
                
                #print(f"Opções para {col}: {filter_options[col]}")

            # --- APLICA ORDENAÇÃO --- 
            sort_column = sort_info.get('column', 'data')
            sort_direction = sort_info.get('direction', 'asc')
            sort_prefix = "-" if sort_direction == 'desc' else ""

            if sort_column in ALLOWED_SORT_COLUMNS:
                # Verifica se a coluna de ordenação é visível para o usuário
                if sort_column in visible_columns:
                    #print(f"Aplicando ordenação: {sort_prefix}{sort_column}")
                    queryset = queryset.order_by(f"{sort_prefix}{sort_column}")
                else:
                    #print(f"Coluna de ordenação '{sort_column}' não visível. Usando ordenação padrão por 'data'.")
                    queryset = queryset.order_by("data") # Ordenação padrão se a coluna não for visível
            else:
                #print(f"Coluna de ordenação inválida: {sort_column}. Usando ordenação padrão por 'data'.")
                queryset = queryset.order_by("data")

            # --- PREPARA DADOS PARA RESPOSTA JSON --- 
            #print(f"Campos a serem retornados: {visible_columns}")
            filtered_records = list(queryset.values(*visible_columns))
            #print(f"Número final de registros a serem enviados: {len(filtered_records)}")

            # Processa os registros para formatação final (status, datas)
            num_index = 0
            for record in filtered_records:
                record['id'] = queryset[num_index].id
                if len(queryset) > num_index:
                    num_index += 1
                if 'status' in record and record['status'] in STATUS_MAP_REVERSED:
                    record['status'] = STATUS_MAP_REVERSED[record['status']]
                
                for date_col in DATE_COLUMNS:
                    if date_col in record:
                        if isinstance(record[date_col], (datetime, date)):
                            record[date_col] = record[date_col].strftime('%Y-%m-%d')
                        elif record[date_col] is None:
                             record[date_col] = '' # Garante string vazia para None
            
            #print("--- filter_data_view FINALIZADA COM SUCESSO ---")
            return JsonResponse({
                'records': filtered_records,
                'filter_options': filter_options, # Inclui as opções de filtro
                'has_full_permission': has_full_permission
            })

        except json.JSONDecodeError:
            #print("Erro: JSON inválido recebido.")
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        except Exception as e:
            #print(f"Erro interno ao processar requisição de filtro: {e}")
            import traceback
            #print(traceback.format_exc()) # Imprime traceback para debug
            return JsonResponse({'error': 'Erro interno do servidor'}, status=500)

    #print("--- filter_data_view FINALIZADA - MÉTODO INVÁLIDO ---")
    return JsonResponse({'error': 'Método de requisição inválido, esperado POST'}, status=405)

# --- Outras views (login, cadastrar_pais) --- 
# (Mantidas como antes)
def login(request):
    if request.method == "GET":
        next_url = request.GET.get('next', None)
        context = {'next': next_url} if next_url else {}
        return render(request, 'ocorrencia/login.html', context)
    else:
        country_name = request.POST.get('country', '').strip().capitalize()
        country_pass = request.POST.get('password', '')
        next_url = request.POST.get('next', None)

        # Tenta autenticar com capitalizado
        user = authenticate(request, username=country_name, password=country_pass)

        # Se falhar, tenta com nome em maiúsculas
        if user is None:
            user = authenticate(request, username=country_name.upper(), password=country_pass)

        if user is not None:
            login_django(request, user)
            return redirect(next_url) if next_url else redirect('/ocorrencia')
        else:
            messages.error(request, "Usuário ou senha inválidos.")
            return redirect(f"{reverse('login_ocorrencias')}?next={next_url}" if next_url else 'login_ocorrencias')

def cadastrar_pais(request):
    if not request.user.is_superuser:
        messages.error(request, "Você precisa ser superusuário para cadastrar um novo país.")
        return redirect('/ocorrencia')

    if request.method == "GET":
        return render(request, 'ocorrencia/cadastrar.html')

    country_name = request.POST.get('country', '').upper().strip()
    country_pass = request.POST.get('password', '')

    if not country_name or not country_pass:
        messages.error(request, "Nome do país e senha são obrigatórios.")
        return redirect('cadastrar_pais')

    if User.objects.filter(username=country_name).exists():
        messages.warning(request, "Esse país já está cadastrado.")
        return redirect('cadastrar_pais')

    try:
        User.objects.create_user(username=country_name, password=country_pass)
        messages.success(request, f"País '{country_name}' cadastrado com sucesso!")
        return redirect('/ocorrencia')
    except Exception as e:
        messages.error(request, f"Erro ao cadastrar país: {str(e)}")
        return redirect('cadastrar_pais')

@login_required
def subir_ocorrencia(request):
    has_full_permission = request.user.is_superuser
    
    if request.method == 'POST':
        if has_full_permission:
            country = request.POST.get("country")
        else:
            country = request.user
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

        
        ocorrencia = Record.objects.create(
            technical = tecnico,
            responsible= responsavel,
            device= equipamento,
            area= area,
            serial= serial,
            brand= marca,
            model= modelo,
            year=ano,
            country= country,
            version= versao,
            problem_detected=problema,
        )

        return HttpResponse("Cadastrado", status=201)

    return render(request, 'ocorrencia/subir_ocorrencia.html')

@login_required(login_url=URL_LOGIN)
def alterar_dados(request):
    if request.method == 'POST':
        field_name = request.POST.get('field')
        new_value = request.POST.get('value')
        if field_name in DATE_COLUMNS:
            print("data a vista")
            new_value = datetime.strptime(new_value, '%d/%m/%Y').date()
        record = Record.objects.get(id=request.POST.get('id'))
        print(new_value)
        try:
            # Atualiza o campo dinamicamente
            print(field_name)
            setattr(record, field_name, new_value)
            record.save(update_fields=[field_name])
            print(record)
            return JsonResponse({
                'status': 'success',
                'new_display': new_value  # Ajuste conforme o campo
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error'}, status=405)