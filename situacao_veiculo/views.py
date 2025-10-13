from django.shortcuts import render, redirect
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
                    'vencimento_dias': cliente._vencimento_dias,
                    'status_message': cliente.status_message,
                })
            
            context['clientes_duplicados'] = lista_clientes
            context['mensagem'] = 'Encontradas múltiplas ocorrências para esse serial. Verifique os dados abaixo:'
            return render(request, 'situacao/index.html', context)
        
        cliente = clientes.first()
        context['cliente'] = cliente
        context['status'] = cliente.status
        context['mensagem'] = cliente.status_message
        context['status_message'] = cliente.status_message
        
        return render(request, 'situacao/index.html', context)
    
    return redirect('index')  # Redireciona se acessado via GET


def index(request):
    return render(request, 'situacao/index.html', {'clientes': None})

