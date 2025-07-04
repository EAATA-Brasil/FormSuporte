from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from .forms import VeiculoForm
from .models import Veiculo
from django.db.models import Q
from django.core.paginator import Paginator

def cadastrar_veiculo(request):
    if request.method == 'POST':
        form = VeiculoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Veículo cadastrado com sucesso!')
            return redirect('index_form')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = VeiculoForm()
    
    return render(request, 'form/create.html', {'form': form})

def index(request):
    filtros = Q()
    
    # Filtros com ordenação
    if request.GET.get('pais'):
        filtros &= Q(pais__icontains=request.GET['pais'])
    if request.GET.get('brand'):
        filtros &= Q(brand__icontains=request.GET['brand'])
    if request.GET.get('modelo'):
        filtros &= Q(modelo__icontains=request.GET['modelo'])
    if request.GET.get('ano'):
        filtros &= Q(ano__icontains=request.GET['ano'])
    
    veiculos = Veiculo.objects.filter(filtros).order_by('pais', 'brand', 'modelo', 'ano')

    # Paginação
    paginator = Paginator(object_list=veiculos, per_page=10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'form/index.html', {
        'page_obj': page_obj,
        'filtros': request.GET,
    })

def get_opcoes_filtro(request):
    pais = request.GET.get('pais', '')
    marca = request.GET.get('marca', '')
    
    resultados = Veiculo.objects.all()
    
    if pais:
        resultados = resultados.filter(pais__icontains=pais)
    if marca:
        resultados = resultados.filter(brand__icontains=marca)
    
    data = {
        'pais': list(resultados.order_by('pais').values_list('pais', flat=True).distinct()),
        'marcas': list(resultados.order_by('brand').values_list('brand', flat=True).distinct()),
        'modelos': list(resultados.order_by('modelo').values_list('modelo', flat=True).distinct()),
        'anos': list(resultados.order_by('ano').values_list('ano', flat=True).distinct()),
    }
    return JsonResponse(data)

def update_vehicle(request):
    if request.method == 'POST':
        try:
            veiculo = Veiculo.objects.get(id=request.POST.get('id'))
            field_name = request.POST.get('field')
            new_value = request.POST.get('value')
            
            setattr(veiculo, field_name, new_value)
            veiculo.save()
            
            return JsonResponse({
                'status': 'success',
                'new_display': new_value
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error'}, status=405)

def update_vehicle_field(request):
    if request.method == 'POST':
        veiculo_id = request.POST.get('id')
        field_name = request.POST.get('field')
        new_value = request.POST.get('value')
        
        try:
            veiculo = Veiculo.objects.get(id=veiculo_id)
            setattr(veiculo, field_name, new_value)
            veiculo.save(update_fields=[field_name])

            response_data = {
                'status': 'success',
                'new_value': new_value,
                'display_value': getattr(veiculo, f'get_{field_name}_display', lambda: None)()
            }

            return JsonResponse(response_data)
        except Veiculo.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Veículo não encontrado'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        
    return JsonResponse({'status': 'error'}, status=405)