# -*- coding: utf-8 -*-

# Imports de bibliotecas padrão
import os
import sys
import json
from datetime import datetime

# Imports do Django REST Framework
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

# Imports do Django
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.conf import settings

# Imports locais da aplicação
from .models import Equipamentos, TipoEquipamento, MarcaEquipamento
from .serializers import EquipamentosSerializer, TipoEquipamentoSerializer, MarcaEquipamentoSerializer

# --- Configuração WeasyPrint --- #

# Tenta configurar o GTK3-Runtime para WeasyPrint em ambientes Windows.
# Em Linux, WeasyPrint geralmente funciona nativamente.
if sys.platform == 'win32':
    try:
        # Lista de possíveis caminhos de instalação do GTK3-Runtime.
        gtk_paths = [
            r'C:\Program Files\GTK3-Runtime Win64\bin',
            r'C:\Program Files (x86)\GTK3-Runtime Win64\bin',
            r'C:\gtk\bin',
        ]
        
        # Adiciona o caminho do GTK3 ao PATH do sistema se encontrado.
        for path in gtk_paths:
            if os.path.exists(path):
                os.add_dll_directory(path) # Para Python 3.8+
                os.environ['PATH'] = path + os.pathsep + os.environ['PATH']
                print(f"GTK3-Runtime encontrado e configurado em: {path}")
                break
        else:
            print("Aviso: GTK3-Runtime para WeasyPrint não encontrado em caminhos padrão.")
    except Exception as e:
        print(f"Erro na configuração do GTK para WeasyPrint: {e}")
elif sys.platform.startswith('linux'):
    print("Ambiente Linux detectado. WeasyPrint deve funcionar nativamente.")

# Verifica a disponibilidade do WeasyPrint.
try:
    from weasyprint import HTML
    from weasyprint.text.fonts import FontConfiguration
    WEASYPRINT_AVAILABLE = True
    print("WeasyPrint disponível.")
except ImportError:
    WEASYPRINT_AVAILABLE = False
    print("Aviso: WeasyPrint não está instalado ou configurado corretamente. A geração de PDF pode falhar.")

# --- ViewSets para a API REST --- #

class EquipamentosViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para listar e recuperar equipamentos.
    Permite apenas operações de leitura (GET).
    """
    queryset = Equipamentos.objects.all().order_by('nome')
    serializer_class = EquipamentosSerializer

class TipoEquipamentoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para listar e recuperar tipos de equipamento.
    Permite apenas operações de leitura (GET).
    """
    queryset = TipoEquipamento.objects.all().order_by('nome')
    serializer_class = TipoEquipamentoSerializer

class MarcaEquipamentoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para listar e recuperar marcas de equipamento.
    Permite apenas operações de leitura (GET).
    """
    queryset = MarcaEquipamento.objects.all().order_by('nome')
    serializer_class = MarcaEquipamentoSerializer

# --- Funções Auxiliares --- #

def format_currency(value):
    """
    Formata um valor numérico para o formato de moeda brasileira (R$ X.XXX,XX).

    Args:
        value (float or str): O valor a ser formatado.

    Returns:
        str: O valor formatado como moeda brasileira. Retorna "R$ 0,00" em caso de erro.
    """
    try:
        value = float(value)
        # Formatação manual para garantir o padrão brasileiro.
        return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except (ValueError, TypeError):
        return "R$ 0,00"

def _html_to_pdf_weasyprint(html_string):
    """
    Converte uma string HTML em um documento PDF usando WeasyPrint.

    Args:
        html_string (str): A string HTML a ser convertida.

    Returns:
        bytes: Os dados do PDF em bytes, ou None se WeasyPrint não estiver disponível
               ou ocorrer um erro.
    """
    if not WEASYPRINT_AVAILABLE:
        print("Erro: WeasyPrint não está disponível. Não é possível gerar PDF.")
        return None
    
    try:
        font_config = FontConfiguration()
        # Define a base URL para que o WeasyPrint possa encontrar recursos como CSS e imagens.
        base_url = str(settings.BASE_DIR) if settings.DEBUG else settings.STATIC_URL
        
        html = HTML(string=html_string, base_url=base_url)
        pdf_data = html.write_pdf(font_config=font_config)
        
        return pdf_data
        
    except Exception as e:
        print(f"Erro ao gerar PDF com WeasyPrint: {e}")
        return None

def _calculate_item_value(equipamento, quantidade, localizacao, faturamento):
    """
    Calcula o valor unitário e total de um item de equipamento com base na localização e faturamento.
    """
    if localizacao == 'SP':
        valor_unitario = float(equipamento.custo_geral)
    else:
        if faturamento == 'CPF':
            valor_unitario = float(equipamento.custo_cpf)
        else:
            valor_unitario = float(equipamento.custo_cnpj)
    
    valor_total_item = valor_unitario * quantidade
    
    return {
        'nome': equipamento.nome,
        'valor_unitario': valor_unitario,
        'valor_unitario_formatado': format_currency(valor_unitario),
        'quantidade': quantidade,
        'valor_total': valor_total_item,
        'valor_total_formatado': format_currency(valor_total_item)
    }

def _process_equipamentos_data(equipamento_ids, quantidades, localizacao, faturamento):
    """
    Processa os dados dos equipamentos para a geração do PDF.
    """
    equipamentos_data = []
    for i, equipamento_id in enumerate(equipamento_ids):
        try:
            equipamento = Equipamentos.objects.get(id=equipamento_id)
            quantidade = int(quantidades[i]) if i < len(quantidades) else 1
            
            item_data = _calculate_item_value(equipamento, quantidade, localizacao, faturamento)
            equipamentos_data.append(item_data)
        except Equipamentos.DoesNotExist:
            print(f"Aviso: Equipamento com ID {equipamento_id} não encontrado.")
            continue
    return equipamentos_data

def _calculate_totals(equipamentos_data, desconto_valor, entrada_valor, valor_parcela):
    """
    Calcula os totais da simulação de venda.
    """
    valor_total_equipamentos = sum(item['valor_total'] for item in equipamentos_data)
    valor_total_final = valor_total_equipamentos - desconto_valor
    
    return {
        'valorTotal': valor_total_equipamentos,
        'valorTotal_formatado': format_currency(valor_total_equipamentos),
        'valorTotalFinal': valor_total_final,
        'valorTotalFinal_formatado': format_currency(valor_total_final),
        'desconto': desconto_valor,
        'desconto_formatado': format_currency(desconto_valor),
        'entrada': entrada_valor,
        'entrada_formatado': format_currency(entrada_valor),
        'valorParcela': valor_parcela,
        'valorParcela_formatado': format_currency(valor_parcela),
    }

def _get_report_dates():
    """
    Retorna as datas de geração e validade do relatório.
    """
    hoje = datetime.now()
    # A validade é definida para o primeiro dia do próximo mês.
    if hoje.month == 12:
        validade = datetime(hoje.year + 1, 1, 1)
    else:
        validade = datetime(hoje.year, hoje.month + 1, 1)
    
    return {
        'dataGeracao': hoje.strftime('%d/%m/%Y'),
        'horaGeracao': hoje.strftime('%H:%M'),
        'validadeRelatorio': validade.strftime('%d/%m/%Y'),
    }

# --- Views da API --- #

@api_view(['POST'])
def generate_pdf(request):
    """
    Endpoint da API para gerar um PDF de simulação de venda.

    Recebe dados de simulação via POST, processa os equipamentos,
    calcula totais e gera um PDF formatado com WeasyPrint.
    Em caso de falha na geração do PDF, um HTML é retornado para debug.

    Args:
        request (HttpRequest): A requisição POST contendo os dados da simulação.

    Returns:
        HttpResponse: Um FileResponse contendo o PDF gerado ou um HttpResponse
                      com o HTML para debug.
        Response: Um objeto Response com erro em caso de falha no processamento.
    """
    try:
        data = request.data
        
        # Extrai e converte valores numéricos com tratamento de erro.
        desconto_valor = float(data.get('desconto', 0))
        entrada_valor = float(data.get('entrada', 0))
        valor_parcela = float(data.get('valorParcela', 0))
        parcelas = int(data.get('parcelas', 0))

        # Processa os dados dos equipamentos.
        equipamentos_data = _process_equipamentos_data(
            data.get('equipamentos', []),
            data.get('quantidades', []),
            data.get('localizacao', ''),
            data.get('faturamento', '')
        )
        
        # Calcula os totais da simulação.
        totals = _calculate_totals(equipamentos_data, desconto_valor, entrada_valor, valor_parcela)
        report_dates = _get_report_dates()

        # Prepara todos os dados para o template HTML.
        template_data = {
            **totals,
            **report_dates,
            'equipamentos': equipamentos_data,
            'localizacao': data.get('localizacao', ''),
            'faturamento': data.get('faturamento', ''),
            'observacao': data.get('observacao', ''), # Observação já é tratada como HTML seguro
            'descricao': data.get('descricao', ''),
            'tipoPagamento': data.get('tipoPagamento', ''),
            'nomeVendedor': data.get('nomeVendedor', ''),
            'nomeCNPJ': data.get('nomeCNPJ', ''),
            'nomeCliente': data.get('nomeCliente', ''),
            'parcelas': parcelas,
        }
        
        # Renderiza o template HTML.
        html_string = render_to_string('api/pdf_simulador.html', template_data)
        
        # Converte o HTML para PDF.
        pdf = _html_to_pdf_weasyprint(html_string)
        
        if pdf:
            # Retorna o PDF como um anexo.
            response = HttpResponse(pdf, content_type='application/pdf')
            filename = f"Simulacao_de_Venda_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        else:
            # Em caso de falha na geração do PDF, retorna o HTML para depuração.
            print("Falha na geração do PDF, retornando HTML.")
            response = HttpResponse(html_string, content_type='text/html')
            filename = f"Simulacao_HTML_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.html"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        
    except json.JSONDecodeError:
        return Response({'error': 'JSON inválido no corpo da requisição.'}, status=400)
    except Exception as e:
        print(f"Erro inesperado na geração do PDF: {e}")
        return Response({'error': f'Ocorreu um erro inesperado: {e}'}, status=500)

# Função de compatibilidade (mantida para evitar quebras em código legado, se houver).
def html_to_pdf(html_string):
    """
    Função de compatibilidade para _html_to_pdf_weasyprint.
    DEPRECATED: Use _html_to_pdf_weasyprint diretamente.
    """
    return _html_to_pdf_weasyprint(html_string)

