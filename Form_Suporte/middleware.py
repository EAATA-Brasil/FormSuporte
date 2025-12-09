from __future__ import annotations

from time import perf_counter
from typing import Callable

from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin

from .metrics import REQUEST_COUNT, REQUEST_LATENCY


class RequestMetricsMiddleware(MiddlewareMixin):
    """Coleta métricas básicas de requisições HTTP para o Prometheus."""

    def process_view(
        self,
        request: HttpRequest,
        view_func: Callable,
        view_args: list,
        view_kwargs: dict,
    ) -> None:
        request._metrics_start_time = perf_counter()
        request._metrics_view = f"{view_func.__module__}.{view_func.__name__}"

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        self._observe_metrics(request, getattr(response, "status_code", 0))
        return response

    def process_exception(self, request: HttpRequest, exception: Exception) -> None:
        # Incrementa o contador mesmo quando a resposta é 500.
        self._observe_metrics(request, 500)

    def _observe_metrics(self, request: HttpRequest, status_code: int) -> None:
        method = getattr(request, "method", "unknown")
        endpoint = getattr(request, "_metrics_view", getattr(request, "path", "unknown"))
        status_label = str(status_code)

        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status_label).inc()

        start_time = getattr(request, "_metrics_start_time", None)
        if start_time is not None:
            REQUEST_LATENCY.labels(endpoint=endpoint, method=method).observe(
                perf_counter() - start_time
            )

