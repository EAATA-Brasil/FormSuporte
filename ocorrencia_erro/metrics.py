from prometheus_client import Counter, Histogram, Gauge

# ---- MÉTRICAS DE EVENTO (Counters) ----
REGISTROS_CRIADOS = Counter(
    "ocorrencias_registradas_total",
    "Quantidade total de ocorrências criadas"
)

REGISTROS_ATUALIZADOS = Counter(
    "ocorrencias_atualizadas_total",
    "Quantidade total de edições realizadas em ocorrências",
    ["campo"]     # ← armazena qual campo foi editado
)

ARQUIVOS_ENVIADOS = Counter(
    "ocorrencia_arquivos_enviados_total",
    "Total de arquivos enviados"
)

ARQUIVOS_BAIXADOS = Counter(
    "ocorrencia_arquivos_baixados_total",
    "Total de downloads de arquivos"
)

LOGIN_SUCESSO = Counter(
    "ocorrencia_logins_sucesso_total",
    "Total de logins bem-sucedidos"
)

LOGIN_ERRO = Counter(
    "ocorrencia_logins_falha_total",
    "Total de logins com falha"
)

# ---- MÉTRICA ESPECÍFICA DE RESOLUÇÃO ----
TEMPO_RESOLUCAO = Histogram(
    "ocorrencia_tempo_resolucao_segundos",
    "Tempo entre criar e resolver uma ocorrência"
)

# ---- MÉTRICAS DE ESTADO (Gauge) ----
REGISTROS_EXISTENTES = Gauge(
    "ocorrencias_existentes_total",
    "Quantidade total de ocorrências existentes no banco"
)
