from prometheus_client import Counter

SIMULACOES_TOTAL = Counter(
    "simulador_execucoes_total",
    "Total de execuções do simulador"
)
