from prometheus_client import Counter, Histogram, Gauge

# ---- MÉTRICAS DE REQUISIÇÃO ----

API_REQUESTS = Counter(
    "api_requests_total",
    "Total de requisições recebidas na API",
    ["endpoint", "method", "status"]
)

API_LATENCY = Histogram(
    "api_request_latency_seconds",
    "Tempo de resposta por endpoint",
    ["endpoint", "method"]
)

# ---- MÉTRICAS DE NEGÓCIO ----

PDF_GERADO = Counter(
    "api_pdf_gerado_total",
    "Quantidade total de PDFs gerados"
)

PDF_FALHA = Counter(
    "api_pdf_falha_total",
    "Falhas ao gerar PDF"
)

HTML_FALLBACK = Counter(
    "api_pdf_fallback_html_total",
    "Quantidade de respostas HTML devido a falha ou ausência de WeasyPrint"
)

# contagem de entidades do banco
TOTAL_EQUIPAMENTOS = Gauge(
    "api_total_equipamentos",
    "Quantidade de equipamentos cadastrados"
)

TOTAL_TIPOS = Gauge(
    "api_total_tipos_equipamento",
    "Quantidade de tipos de equipamento cadastrados"
)

TOTAL_MARCAS = Gauge(
    "api_total_marcas_equipamento",
    "Quantidade de marcas cadastradas"
)
