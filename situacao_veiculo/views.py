from django.shortcuts import render, redirect
from .models import Cliente
from datetime import datetime, date

def buscar_serial(request):
    context = {}
    if request.method == 'POST':
        serial = request.POST.get('serial', '').strip()
        context['serial_digitado'] = serial
        try:
            cliente = Cliente.objects.get(serial=serial)
            context['cliente'] = cliente

            
            context['mensagem'] = 'Passar para o comercial atualizar o cadastro.'
            # vencimento = date- cliente.vencimento.day
            data1 = datetime.strptime(str(cliente.vencimento).replace('-','/'), "%Y/%m/%d")
            data2 = datetime.strptime(str(date.today()).replace('-','/'), "%Y/%m/%d")

            vencimento = (data1 - data2).days
            if vencimento > 30:
                context['status'] = 'direito'
                context['mensagem'] = "Atender normalmente"
                context['status_message'] = "SUPORTE LIBERADO"
            elif vencimento < 1:
                context['status'] = 'vencido'
                context['mensagem'] = "Não fazer atendimento - BLOQUEADO"
                context['status_message'] = "SUPORTE VENCIDO"
            else:
                context['status'] = 'vencendo'
                context['mensagem'] = "Atender normalmente - Passar para o comercial"
                context['status_message'] = "SUPORTE A VENCER"

            return render(request, 'situacao/index.html', context)
        
        except Cliente.DoesNotExist:
            return render(request, 'situacao/index.html', {
                'status_message':'SEM DADOS',
                'mensagem': 'Passar para o comercial atualizar o cadastro.'
            })
    return redirect('index')  # Redireciona se acessado via GET

def index(request):
    # Pode manter esta view para exibir todos os clientes inicialmente
    return render(request, 'situacao/index.html', {'clientes': None})