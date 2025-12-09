from __future__ import annotations

"""Prometheus metric definitions shared across the project."""

from prometheus_client import Counter, Histogram

# Contabiliza requisições HTTP agrupadas por método, endpoint e status code.
REQUEST_COUNT = Counter(
    "form_suporte_http_requests_total",
    "Total de requisições HTTP recebidas pelo FormSuporte",
    labelnames=["method", "endpoint", "status"],
)

# Mede a latência das requisições para ajudar a identificar rotas mais lentas.
REQUEST_LATENCY = Histogram(
    "form_suporte_http_request_duration_seconds",
    "Tempo de resposta das requisições HTTP",
    labelnames=["endpoint", "method"],
)

