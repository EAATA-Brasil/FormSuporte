from django.http import HttpResponse
from django.shortcuts import render
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest


def index(req):
    return render(req, "home/index.html")


def metrics(_req):
    """Exibe as métricas do Prometheus para coleta pelo Grafana."""

    return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)
