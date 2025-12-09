# views.py
from django.shortcuts import render
from .metrics import SIMULACOES_TOTAL

def index(request):
    SIMULACOES_TOTAL.inc()
    return render(request, 'simulador/index.html')
