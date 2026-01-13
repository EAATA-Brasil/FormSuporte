# views.py - Lógica de Views e API para o App 'API'

import os
import sys
from datetime import datetime

from django.http import HttpResponse
from django.template.loader import render_to_string
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from rest_framework import viewsets
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from .models import Equipamentos, TipoEquipamento, MarcaEquipamento
from .serializers import EquipamentosSerializer, TipoEquipamentoSerializer, MarcaEquipamentoSerializer, ClienteSerializer
from situacao_veiculo.models import Cliente

import re
import unicodedata
from urllib.parse import quote

def sanitize_filename_component(value: str, max_len: int = 80) -> str:
    """
    Sanitiza uma parte do nome do arquivo:
    - remove caracteres inválidos: \ / : * ? " < > |
    - remove controles e trim
    - troca espaços por underscore
    - limita tamanho
    """
    if not value:
        return ""

    # garante string
    s = str(value).strip()

    # remove caracteres de controle (0x00-0x1F, 0x7F)
    s = re.sub(r"[\x00-\x1f\x7f]", "", s)

    # remove caracteres inválidos em filenames (Windows)
    s = re.sub(r'[\\/:*?"<>|]+', "", s)

    # colapsa espaços e troca por underscore
    s = re.sub(r"\s+", "_", s)

    # evita nomes só com pontos/underscores
    s = s.strip("._ ")

    # limita tamanho
    if len(s) > max_len:
        s = s[:max_len].rstrip("._ ")

    return s


def ascii_fallback(value: str) -> str:
    """
    Faz um fallback ASCII (sem acentos) para browsers que não suportam filename*.
    """
    if not value:
        return ""
    nfkd = unicodedata.normalize("NFKD", value)
    return "".join(c for c in nfkd if ord(c) < 128)

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

class TipoEquipamentoViewSet(viewsets.ReadOnlyModelViewSet):
    """API ViewSet para listar e recuperar tipos de equipamento (somente leitura)."""
    queryset = TipoEquipamento.objects.all().order_by('nome')
    serializer_class = TipoEquipamentoSerializer

class MarcaEquipamentoViewSet(viewsets.ReadOnlyModelViewSet):
    """API ViewSet para listar e recuperar marcas de equipamento (somente leitura)."""
    queryset = MarcaEquipamento.objects.all().order_by('nome')
    serializer_class = MarcaEquipamentoSerializer

class ClienteViewSet(viewsets.ReadOnlyModelViewSet):
    """API ViewSet para listar e recuperar clientes (somente leitura)."""
    queryset = Cliente.objects.all().order_by('serial')
    serializer_class = ClienteSerializer


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
        
        usar_precos_cliente = bool(data.get("usarPrecosCliente"))
        itens_pdf = data.get("itensPDF") or []

        equipamentos_data = []
        valor_total_sem_taxa = None  # será preenchido quando vier do cliente
        equipamento_ids = data.get("equipamentos", [])
        quantidades = data.get("quantidades", [])
        if usar_precos_cliente and isinstance(itens_pdf, list) and len(itens_pdf) > 0:
            # ✅ usa os preços já calculados no cliente (taxados)
            valor_total_sem_taxa = 0.0
            for item in itens_pdf:
                try:
                    nome = item.get("nome") or "Equipamento"
                    qtd = int(item.get("quantidade") or 1)

                    valor_total = float(item.get("valorTotal") or 0)
                    valor_unit = float(item.get("valorUnitario") or (valor_total / qtd if qtd else 0))

                    valor_base_total = float(item.get("valorBaseTotal") or 0)
                    valor_total_sem_taxa += valor_base_total

                    equipamentos_data.append({
                        "nome": nome,
                        "valor_unitario": valor_unit,
                        "valor_unitario_formatado": format_currency(valor_unit),
                        "quantidade": qtd,
                        "valor_total": valor_total,
                        "valor_total_formatado": format_currency(valor_total),
                    })
                except Exception:
                    continue
        else:
            # 🔁 fallback: comportamento antigo (recalcula do banco)
            for i, equipamento_id in enumerate(equipamento_ids):
                try:
                    try:
                        quantidade = int(quantidades[i])
                    except (ValueError, TypeError, IndexError):
                        quantidade = 1

                    equipamento = Equipamentos.objects.get(id=equipamento_id)

                    localizacao = data.get("localizacao")
                    faturamento = data.get("faturamento")

                    if localizacao == "SP":
                        valor_unitario = float(equipamento.custo_geral)
                    elif faturamento == "CPF":
                        valor_unitario = float(equipamento.custo_cpf)
                    else:
                        valor_unitario = float(equipamento.custo_cnpj)

                    valor_total_item = valor_unitario * quantidade

                    equipamentos_data.append({
                        "nome": equipamento.nome,
                        "valor_unitario": valor_unitario,
                        "valor_unitario_formatado": format_currency(valor_unitario),
                        "quantidade": quantidade,
                        "valor_total": valor_total_item,
                        "valor_total_formatado": format_currency(valor_total_item),
                    })
                except Exception:
                    continue

        # ✅ subtotal exibido: se o cliente mandou, use ele
        subtotal_exib = data.get("subtotalEquipamentosExibicao", None)
        try:
            subtotal_exib = float(subtotal_exib) if subtotal_exib is not None else None
        except Exception:
            subtotal_exib = None

        valor_total_equipamentos = subtotal_exib if subtotal_exib is not None else sum(
            item["valor_total"] for item in equipamentos_data
        )

        # ❗ Valor final SEM taxa
        valor_final_sem_taxa = valor_total_sem_taxa if valor_total_sem_taxa is not None else valor_total_equipamentos

        # Garante que desconto e entrada são floats
        desconto_valor = float(data.get('desconto', 0) or 0)
        entrada_valor = float(data.get('entrada', 0) or 0)
        valor_parcela = float(data.get('valorParcela', 0) or 0)
        frete_valor = float(data.get('frete', 0) or 0)

        tem_frete = frete_valor > 0
        valor_total_final = float(data.get("valorTotal") or valor_total_equipamentos)

        # 3. Cálculo das parcelas com ajuste na última parcela (em centavos)
        parcelas_qtd = int(data.get('parcelas', 0) or 0)
        parcela_base = 0.0
        ultima_parcela = 0.0
        parcelas_texto_extra = None
        if parcelas_qtd > 0:
            total_cent = round(valor_total_final * 100)
            entrada_cent = round(entrada_valor * 100)
            saldo_cent = max(0, total_cent - entrada_cent)
            parcela_base_cent = saldo_cent // parcelas_qtd
            resto_cent = saldo_cent - (parcela_base_cent * parcelas_qtd)
            ultima_parcela_cent = parcela_base_cent + resto_cent

            parcela_base = parcela_base_cent / 100.0
            ultima_parcela = ultima_parcela_cent / 100.0
        # Não exibir linha extra no PDF
        parcelas_texto_extra = None

        
        # 4. Preparar Dados para o Template
        template_data = {
            'equipamentos': equipamentos_data,

            'entrada': entrada_valor,
            'entrada_formatado': format_currency(entrada_valor),

            'parcelas': parcelas_qtd,
            'localizacao': data.get('localizacao', ''),
            'faturamento': data.get('faturamento', ''),

            # parcelas: sempre exibir a base inteira; última parcela ajusta o resto
            'valorParcela': parcela_base,
            'valorParcela_formatado': format_currency(parcela_base),
            'ultimaParcela': ultima_parcela,
            'ultimaParcela_formatado': format_currency(ultima_parcela),
            'parcelasTextoExtra': parcelas_texto_extra,

            'valorTotal': valor_total_equipamentos,
            'valorTotal_formatado': format_currency(valor_total_equipamentos),

            'valorTotalFinal': valor_total_final,
            'valorTotalFinal_formatado': format_currency(valor_total_final),

            'desconto': desconto_valor,
            'desconto_formatado': format_currency(desconto_valor),

            'observacao': data.get('observacao', ''),
            'descricao': data.get('descricao', ''),
            'tipoPagamento': data.get('tipoPagamento', ''),
            'nomeVendedor': data.get('nomeVendedor', ''),
            'nomeCNPJ': data.get('nomeCNPJ', ''),
            'nomeCliente': data.get('nomeCliente', ''),

            # subtotal COM taxa (como já está)
            'subtotalEquipamentos': valor_total_equipamentos,
            'subtotalEquipamentos_formatado': format_currency(valor_total_equipamentos),

            # valor final SEM taxa (novo)
            'valorFinalSemTaxa': valor_final_sem_taxa,
            'valorFinalSemTaxa_formatado': format_currency(valor_final_sem_taxa),
        }

        if tem_frete:
            template_data['frete'] = frete_valor
            template_data['frete_formatado'] = format_currency(frete_valor)

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
            # Retorna o PDF como anexo
            response = HttpResponse(pdf, content_type='application/pdf')
            raw_nome = data.get('nomeCliente') or ""
            safe_nome = sanitize_filename_component(raw_nome)

            # Se não tiver nomeCliente válido, cai na data/hora
            suffix = safe_nome or hoje.strftime('%Y-%m-%d_%H-%M')

            # Nome final (com acento)
            filename = f"Simulação_de_Venda_{suffix}.pdf"

            # Fallback ASCII (sem acento) pra browsers antigos
            filename_ascii = ascii_fallback(filename) or f"Simulacao_de_Venda_{hoje.strftime('%Y-%m-%d_%H-%M')}.pdf"

            # Header profissional:
            # - filename* (UTF-8) é o principal
            # - filename (ASCII) é fallback
            quoted = quote(filename)
            response['Content-Disposition'] = (
                f'attachment; filename="{filename_ascii}"; filename*=UTF-8\'\'{quoted}'
            )

            return response

        else:
            # Fallback: retorna o HTML para debug ou se WeasyPrint falhar
            response = HttpResponse(html_string, content_type='text/html')
            filename = f"Simulação_HTML_{hoje.strftime('%Y-%m-%d_%H-%M')}.html"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        
    except Exception as e:
        # Loga o erro e retorna uma resposta de erro 500
        print(f"Erro na geração do PDF: {e}")
        return Response({'error': str(e)}, status=500)

# --- Compatibilidade ---

@csrf_exempt
def html_to_pdf(html_string):
    """Função de compatibilidade para nome antigo, apenas chama html_to_pdf_weasyprint."""
    return html_to_pdf_weasyprint(html_string)