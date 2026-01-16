# views.py - Lógica de Views e API para o App 'API'

import os
import sys
from datetime import datetime

from django.http import HttpResponse
from django.template.loader import render_to_string
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Equipamentos, TipoEquipamento, MarcaEquipamento
from .serializers import EquipamentosSerializer, TipoEquipamentoSerializer, MarcaEquipamentoSerializer

<<<<<<< Updated upstream
from .decorators import api_metrics
from .metrics import PDF_GERADO, PDF_FALHA, HTML_FALLBACK
=======
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.authentication import TokenAuthentication
>>>>>>> Stashed changes

# Configuração de caminhos GTK para Windows (necessário para WeasyPrint no Windows)
if sys.platform == 'win32':
    try:
        # Lista de caminhos comuns onde o GTK pode estar instalado
        gtk_paths = [
            r'C:\Program Files\GTK3-Runtime Win64\bin',
            r'C:\Program Files (x86)\GTK3-Runtime Win64\bin',
            r'C:\gtk\bin',
        ]
        
        # Adiciona o caminho do GTK ao PATH para que o WeasyPrint funcione
        for path in gtk_paths:
            if os.path.exists(path):
                os.add_dll_directory(path)
                os.environ['PATH'] = path + os.pathsep + os.environ['PATH']
                break
    except Exception as e:
        # Imprime erro, mas não impede o resto da aplicação de rodar
        print(f"Erro na configuração do GTK (Windows): {e}")
elif sys.platform.startswith('linux'):
    # No Linux, o WeasyPrint geralmente funciona nativamente se as dependências estiverem instaladas
    print("✅ Ambiente Linux detectado - WeasyPrint funcionará nativamente (se dependências instaladas)")

# --- Configuração de Dependências ---

# Configuração para WeasyPrint (necessário para gerar PDF a partir de HTML)
try:
    from weasyprint import HTML
    from weasyprint.text.fonts import FontConfiguration
    WEASYPRINT_AVAILABLE = True
except ImportError:
    # Se o WeasyPrint não estiver instalado, a funcionalidade de PDF será desativada
    WEASYPRINT_AVAILABLE = False


# --- ViewSets para API REST (ReadOnly) ---

class EquipamentosViewSet(viewsets.ReadOnlyModelViewSet):
    """API ViewSet para listar e recuperar equipamentos (somente leitura)."""
    queryset = Equipamentos.objects.all().order_by('nome')
    serializer_class = EquipamentosSerializer
    permission_classes = [IsAuthenticated]

    @api_metrics("equipamentos_list")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @api_metrics("equipamentos_retrieve")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

class TipoEquipamentoViewSet(viewsets.ReadOnlyModelViewSet):
    """API ViewSet para listar e recuperar tipos de equipamento (somente leitura)."""
    queryset = TipoEquipamento.objects.all().order_by('nome')
    serializer_class = TipoEquipamentoSerializer
<<<<<<< Updated upstream
    @api_metrics("tipoequipamento_list")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @api_metrics("tipoequipamento_retrieve")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
=======
    permission_classes = [IsAuthenticated]
>>>>>>> Stashed changes

class MarcaEquipamentoViewSet(viewsets.ReadOnlyModelViewSet):
    """API ViewSet para listar e recuperar marcas de equipamento (somente leitura)."""
    queryset = MarcaEquipamento.objects.all().order_by('nome')
    serializer_class = MarcaEquipamentoSerializer
<<<<<<< Updated upstream
    @api_metrics("marcaequipamento_list")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

<<<<<<< Updated upstream
    @api_metrics("marcaequipamento_retrieve")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
=======
    permission_classes = [IsAuthenticated]
>>>>>>> Stashed changes
=======
class ClienteViewSet(viewsets.ReadOnlyModelViewSet):
    """API ViewSet para listar e recuperar clientes (somente leitura)."""
    queryset = Cliente.objects.all().order_by('serial')
    serializer_class = ClienteSerializer

@csrf_exempt
@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def cliente_search(request):
    """Endpoint POST que retorna cliente por serial.

    Recebe JSON: {"serial": "..."} e devolve o cliente serializado.
    """
    serial = (request.data.get('serial') or '').strip()
    if not serial:
        return Response({'ok': False, 'message': 'Informe o serial.'}, status=400)
    try:
        cliente = Cliente.objects.get(serial=serial)
    except Cliente.DoesNotExist:
        return Response({'ok': False, 'message': 'Serial não encontrado.'}, status=404)

    serializer = ClienteSerializer(cliente)
    return Response({'ok': True, 'data': serializer.data}, status=200)
>>>>>>> Stashed changes

# --- Funções Utilitárias ---

@csrf_exempt
def format_currency(value):
    """
    Formata um valor numérico para o padrão de moeda brasileira (R$ 1.000,00).
    
    A função usa uma substituição temporária ('X') para trocar a vírgula por ponto
    e o ponto por vírgula, garantindo o formato correto.
    """
    try:
        # Converte o valor para float
        valor_float = float(value)
        # Formata com separador de milhar (,) e duas casas decimais (.)
        formato_eua = f"R$ {valor_float:,.2f}"
        # Troca a vírgula (separador de milhar EUA) por 'X'
        temp_troca = formato_eua.replace(',', 'X')
        # Troca o ponto (separador decimal EUA) por vírgula
        decimal_br = temp_troca.replace('.', ',')
        # Troca 'X' por ponto (separador de milhar BR)
        final_br = decimal_br.replace('X', '.')
        return final_br
    except (ValueError, TypeError):
        # Retorna valor padrão em caso de erro de conversão
        return "R$ 0,00"

@csrf_exempt
def html_to_pdf_weasyprint(html_string):
    """
    Converte uma string HTML para um arquivo PDF binário usando WeasyPrint.
    
    Retorna os dados binários do PDF ou None em caso de falha ou se WeasyPrint não estiver disponível.
    """
    if not WEASYPRINT_AVAILABLE:
        print("WeasyPrint não está disponível. Não é possível gerar PDF.")
        return None
    
    try:
        font_config = FontConfiguration()
        # Define a URL base para resolver caminhos de recursos (CSS, imagens)
        # Usa BASE_DIR em DEBUG para caminhos locais ou STATIC_URL em produção
        base_url = str(settings.BASE_DIR) if settings.DEBUG else settings.STATIC_URL
        
        # Cria o objeto HTML e gera o PDF
        html = HTML(string=html_string, base_url=base_url)
        pdf_data = html.write_pdf(font_config=font_config)
        
        return pdf_data
        
    except Exception as e:
        print(f"Erro ao gerar PDF com WeasyPrint: {e}")
        return None
    
# --- View de Geração de PDF ---

@csrf_exempt
@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def generate_pdf(request):
    """
    Endpoint da API para gerar um PDF de simulação de venda a partir dos dados POST.
    
    Processa os dados dos equipamentos, calcula totais e gera o PDF usando WeasyPrint.
    """
    try:
        # 1. Obter e processar dados da requisição
        data = request.data
        
        equipamentos_data = []
        equipamento_ids = data.get('equipamentos', [])
        quantidades = data.get('quantidades', [])
        
        # 2. Processar cada equipamento
        for i, equipamento_id in enumerate(equipamento_ids):
            try:
                # Garante que a quantidade é um inteiro, padrão 1
                try:
                    quantidade = int(quantidades[i])
                except (ValueError, TypeError, IndexError):
                    quantidade = 1
                equipamento = Equipamentos.objects.get(id=equipamento_id)
                
                # 2.1. Lógica de Cálculo de Valor Unitário
                localizacao = data.get('localizacao')
                faturamento = data.get('faturamento')
                
                if localizacao == 'SP':
                    # Custo geral para SP
                    valor_unitario = float(equipamento.custo_geral)
                elif faturamento == 'CPF':
                    # Custo CPF para outras localizações
                    valor_unitario = float(equipamento.custo_cpf)
                else:
                    # Custo CNPJ (padrão) para outras localizações
                    valor_unitario = float(equipamento.custo_cnpj)
                
                # 2.2. Calcular valor total do item
                valor_total_item = valor_unitario * quantidade
                
                # 2.3. Adicionar dados formatados à lista
                equipamentos_data.append({
                    'nome': equipamento.nome,
                    'valor_unitario': valor_unitario,
                    'valor_unitario_formatado': format_currency(valor_unitario),
                    'quantidade': quantidade,
                    'valor_total': valor_total_item,
                    'valor_total_formatado': format_currency(valor_total_item)
                })
            except Equipamentos.DoesNotExist:
                # Ignora equipamentos que não existem no banco de dados
                continue
            except ValueError:
                # Ignora se a conversão para float falhar
                continue
        
        # 3. Calcular Totais e Valores Finais
        valor_total_equipamentos = sum(item['valor_total'] for item in equipamentos_data)
        
        # Garante que desconto e entrada são floats
        desconto_valor = float(data.get('desconto', 0) or 0)
        entrada_valor = float(data.get('entrada', 0) or 0)
        valor_parcela = float(data.get('valorParcela', 0) or 0)
        
        valor_total_final = valor_total_equipamentos - desconto_valor
        
        # 4. Preparar Dados para o Template
        template_data = {
            'equipamentos': equipamentos_data,
            'entrada': entrada_valor,
            'entrada_formatado': format_currency(entrada_valor),
            'parcelas': int(data.get('parcelas', 0) or 0),
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
            'observacao': data.get('observacao', ''), # Observação já é string
            'descricao': data.get('descricao', ''),
            'tipoPagamento': data.get('tipoPagamento', ''),
            'nomeVendedor': data.get('nomeVendedor', ''),
            'nomeCNPJ': data.get('nomeCNPJ', ''),
            'nomeCliente': data.get('nomeCliente', ''),
        }
        
        # 5. Calcular Datas de Geração e Validade
        hoje = datetime.now()
        
        # Calcula o primeiro dia do próximo mês para a validade
        if hoje.month == 12:
            validade = datetime(hoje.year + 1, 1, 1)
        else:
            validade = datetime(hoje.year, hoje.month + 1, 1)
        
        template_data['validadeRelatorio'] = validade.strftime('%d/%m/%Y')
        template_data['dataGeracao'] = hoje.strftime('%d/%m/%Y')
        template_data['horaGeracao'] = hoje.strftime('%H:%M')
        
        # 6. Renderizar HTML e Gerar PDF
        html_string = render_to_string('api/pdf_simulador.html', template_data)
        pdf = html_to_pdf_weasyprint(html_string)
        
        # 7. Retornar Resposta
        if pdf:
            PDF_GERADO.inc()
            # Retorna o PDF como anexo
            response = HttpResponse(pdf, content_type='application/pdf')
            filename = f"Simulação_de_Venda_{hoje.strftime('%Y-%m-%d_%H-%M')}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        else:
            HTML_FALLBACK.inc()
            # Fallback: retorna o HTML para debug ou se WeasyPrint falhar
            response = HttpResponse(html_string, content_type='text/html')
            filename = f"Simulação_HTML_{hoje.strftime('%Y-%m-%d_%H-%M')}.html"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        
    except Exception as e:
        PDF_FALHA.inc()
        # Loga o erro e retorna uma resposta de erro 500
        print(f"Erro na geração do PDF: {e}")
        return Response({'error': str(e)}, status=500)

# --- Compatibilidade ---

@csrf_exempt
def html_to_pdf(html_string):
    """Função de compatibilidade para nome antigo, apenas chama html_to_pdf_weasyprint."""
    return html_to_pdf_weasyprint(html_string)