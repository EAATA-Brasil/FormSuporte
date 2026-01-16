<<<<<<< Updated upstream
from django.http import HttpResponse
from django.shortcuts import render
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest


def index(req):
    return render(req, "home/index.html")


def metrics(_req):
    """Exibe as métricas do Prometheus para coleta pelo Grafana."""

    return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)
=======
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages


def home(request):
    # Login inline: se POST com credenciais, autentica e redireciona de volta
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Usuário ou senha inválidos.')

    quick_links = []
    if request.user.is_authenticated:
        quick_links = [
            {'label': 'Ocorrências', 'href': '/ocorrencia/'},
            {'label': 'Situação (Serial)', 'href': '/situacao/'},
            {'label': 'Simulador', 'href': '/simulador/'},
            {'label': 'Seriais VCI', 'href': '/seriais/'},
            {'label': 'Form (Veículos)', 'href': '/form/'},
            {'label': 'Pedidos', 'href': '/pedido/'},
            {'label': 'Admin', 'href': '/admin/'},
        ]

    return render(request, 'home/index.html', {
        'quick_links': quick_links,
    })


def logout_home(request):
    logout(request)
    return redirect('home')
>>>>>>> Stashed changes
