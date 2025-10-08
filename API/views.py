# views.py
import os
import sys
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.conf import settings
from .models import Equipamentos, TipoEquipamento, MarcaEquipamento
from .serializers import EquipamentosSerializer, TipoEquipamentoSerializer, MarcaEquipamentoSerializer
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt

# Configuração para WeasyPrint
if sys.platform == 'win32':
    try:
        gtk_paths = [
            r'C:\Program Files\GTK3-Runtime Win64\bin',
            r'C:\Program Files (x86)\GTK3-Runtime Win64\bin',
            r'C:\gtk\bin',
        ]
        
        for path in gtk_paths:
            if os.path.exists(path):
                os.add_dll_directory(path)
                os.environ['PATH'] = path + os.pathsep + os.environ['PATH']
                break
    except Exception as e:
        print(f"Erro na configuração do GTK: {e}")
elif sys.platform.startswith('linux'):
    # Linux funciona nativamente - nada especial necessário
    print("✅ Ambiente Linux detectado - WeasyPrint funcionará nativamente")
    
try:
    from weasyprint import HTML
    from weasyprint.text.fonts import FontConfiguration
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

class EquipamentosViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Equipamentos.objects.all().order_by('nome')
    serializer_class = EquipamentosSerializer

class TipoEquipamentoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TipoEquipamento.objects.all().order_by('nome')
    serializer_class = TipoEquipamentoSerializer

class MarcaEquipamentoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MarcaEquipamento.objects.all().order_by('nome')
    serializer_class = MarcaEquipamentoSerializer

@csrf_exempt
def format_currency(value):
    """Formata valor para moeda brasileira R$ 1.000,00"""
    try:
        value = float(value)
        return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except (ValueError, TypeError):
        return "R$ 0,00"

@csrf_exempt
def html_to_pdf_weasyprint(html_string):
    """Converte HTML para PDF usando WeasyPrint"""
    if not WEASYPRINT_AVAILABLE:
        return None
    
    try:
        font_config = FontConfiguration()
        base_url = str(settings.BASE_DIR) if settings.DEBUG else settings.STATIC_URL
        
        html = HTML(string=html_string, base_url=base_url)
        pdf_data = html.write_pdf(font_config=font_config)
        
        return pdf_data
        
    except Exception as e:
        print(f"Erro ao gerar PDF com WeasyPrint: {e}")
        return None
    
@csrf_exempt
@api_view(['POST'])
def generate_pdf(request):
    """Gera PDF a partir dos dados de simulação"""
    try:
        data = request.data
        
        # Processar equipamentos
        equipamentos_data = []
        equipamento_ids = data.get('equipamentos', [])
        quantidades = data.get('quantidades', [])
        
        for i, equipamento_id in enumerate(equipamento_ids):
            try:
                equipamento = Equipamentos.objects.get(id=equipamento_id)
                quantidade = int(quantidades[i]) if i < len(quantidades) else 1
                
                # Calcular valor unitário baseado na localização e faturamento
                if data.get('localizacao') == 'SP':
                    valor_unitario = float(equipamento.custo_geral)
                else:
                    if data.get('faturamento') == 'CPF':
                        valor_unitario = float(equipamento.custo_cpf)
                    else:
                        valor_unitario = float(equipamento.custo_cnpj)
                
                # Calcular valor total do item
                valor_total_item = valor_unitario * quantidade
                
                equipamentos_data.append({
                    'nome': equipamento.nome,
                    'valor_unitario': valor_unitario,
                    'valor_unitario_formatado': format_currency(valor_unitario),
                    'quantidade': quantidade,
                    'valor_total': valor_total_item,
                    'valor_total_formatado': format_currency(valor_total_item)
                })
            except Equipamentos.DoesNotExist:
                continue
        
        # Calcular totais
        valor_total_equipamentos = sum(item['valor_total'] for item in equipamentos_data)
        desconto_valor = float(data.get('desconto', 0))
        valor_total_final = valor_total_equipamentos - desconto_valor
        entrada_valor = float(data.get('entrada', 0))
        valor_parcela = float(data.get('valorParcela', 0))
        
        # Processar observações (manter HTML seguro)
        observacao = data.get('observacao', '')
        
        # Preparar dados para o template
        template_data = {
            'equipamentos': equipamentos_data,
            'entrada': entrada_valor,
            'entrada_formatado': format_currency(entrada_valor),
            'parcelas': int(data.get('parcelas', 0)),
            'localizacao': data.get('localizacao', ''),
            'faturamento': data.get('faturamento', ''),
            'valorParcela': valor_parcela,
            'valorParcela_formatado': format_currency(valor_parcela),
            'valorTotal': valor_total_equipamentos,
            'valorTotal_formatado': format_currency(valor_total_equipamentos),
            'valorTotalFinal': valor_total_final,
            'valorTotalFinal_formatado': format_currency(valor_total_final),
            'desconto': desconto_valor,
            'desconto_formatado': format_currency(desconto_valor),
            'observacao': observacao,
            'descricao': data.get('descricao', ''),
            'tipoPagamento': data.get('tipoPagamento', ''),
            'nomeVendedor': data.get('nomeVendedor', ''),
            'nomeCNPJ': data.get('nomeCNPJ', ''),
            'nomeCliente': data.get('nomeCliente', ''),
        }
        
        # Calcular data de validade (próximo mês)
        hoje = datetime.now()
        if hoje.month == 12:
            validade = datetime(hoje.year + 1, 1, 1)
        else:
            validade = datetime(hoje.year, hoje.month + 1, 1)
        
        template_data['validadeRelatorio'] = validade.strftime('%d/%m/%Y')
        template_data['dataGeracao'] = hoje.strftime('%d/%m/%Y')
        template_data['horaGeracao'] = hoje.strftime('%H:%M')
        
        # Renderizar template HTML
        html_string = render_to_string('api/pdf_simulador.html', template_data)
        
        # Converter HTML para PDF usando WeasyPrint
        pdf = html_to_pdf_weasyprint(html_string)
        
        if pdf:
            # Configurar resposta HTTP
            response = HttpResponse(pdf, content_type='application/pdf')
            filename = f"Simulação_de_Venda_{hoje.strftime('%Y-%m-%d_%H-%M')}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        else:
            # Fallback: retorna HTML para debug
            response = HttpResponse(html_string, content_type='text/html')
            filename = f"Simulação_HTML_{hoje.strftime('%Y-%m-%d_%H-%M')}.html"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        
    except Exception as e:
        print(f"Erro na geração do PDF: {e}")
        return Response({'error': str(e)}, status=500)

# Função compatível com nome antigo
@csrf_exempt
def html_to_pdf(html_string):
    return html_to_pdf_weasyprint(html_string)