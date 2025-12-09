from prometheus_client import Counter, Histogram, Gauge

# --- EVENTOS ---

VEICULOS_CADASTRADOS = Counter(
    "form_veiculos_cadastrados_total",
    "Total de veículos cadastrados"
)

VEICULOS_ATUALIZADOS = Counter(
    "form_veiculos_atualizados_total",
    "Total de campos atualizados em veículos",
    ["campo"]
)

VEICULOS_ATUALIZACAO_ERRO = Counter(
    "form_veiculos_atualizacao_erro_total",
    "Erros ao atualizar veículos"
)

FILTROS_CONSULTADOS = Counter(
    "form_filtros_consultados_total",
    "Quantidade de vezes que filtros foram consultados"
)

# --- AJAX ---
AJAX_FILTRO = Counter(
    "form_ajax_filtro_total",
    "Quantidade de requisições AJAX ao filtro"
)

# --- LATÊNCIA ---

FORM_LATENCIA = Histogram(
    "form_view_latency_seconds",
    "Latência de views do app form",
    ["endpoint", "method"]
)

# --- ESTADO ---

VEICULOS_EXISTENTES = Gauge(
    "form_veiculos_existentes_total",
    "Quantidade total de veículos cadastrados no banco"
)
