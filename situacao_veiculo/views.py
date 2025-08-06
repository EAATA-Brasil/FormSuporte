from django.shortcuts import render, redirect
from .models import Cliente
from datetime import datetime, date

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
            # Há duplicatas - mostrar lista com status de cada um
            lista_clientes = []
            hoje = date.today()
            for cliente in clientes:
                data_vencimento = cliente.vencimento
                vencimento_dias = (data_vencimento - hoje).days
                
                if vencimento_dias > 30:
                    status = 'direito'
                    mensagem_status = "SUPORTE LIBERADO - Atender normalmente"
                elif vencimento_dias < 1:
                    status = 'vencido'
                    mensagem_status = "SUPORTE VENCIDO - Não fazer atendimento - BLOQUEADO"
                else:
                    status = 'vencendo'
                    mensagem_status = "SUPORTE A VENCER - Atender normalmente - Passar para o comercial"
                
                lista_clientes.append({
                    'cliente': cliente,
                    'status': status,
                    'vencimento_dias': vencimento_dias,
                    'status_message': mensagem_status,
                })
            
            context['clientes_duplicados'] = lista_clientes
            context['mensagem'] = 'Encontradas múltiplas ocorrências para esse serial. Verifique os dados abaixo:'
            return render(request, 'situacao/index.html', context)
        
        # Caso tenha exatamente 1 cliente, continua igual antes
        cliente = clientes.first()
        context['cliente'] = cliente
        
        hoje = date.today()
        vencimento_dias = (cliente.vencimento - hoje).days
        
        if vencimento_dias > 30:
            context['status'] = 'direito'
            context['mensagem'] = "Atender normalmente"
            context['status_message'] = "SUPORTE LIBERADO"
        elif vencimento_dias < 1:
            context['status'] = 'vencido'
            context['mensagem'] = "Não fazer atendimento - BLOQUEADO"
            context['status_message'] = "SUPORTE VENCIDO"
        else:
            context['status'] = 'vencendo'
            context['mensagem'] = "Atender normalmente - Passar para o comercial"
            context['status_message'] = "SUPORTE A VENCER"
        
        return render(request, 'situacao/index.html', context)
    
    return redirect('index')  # Redireciona se acessado via GET


def index(request):
    # Pode manter esta view para exibir todos os clientes inicialmente
    return render(request, 'situacao/index.html', {'clientes': None})