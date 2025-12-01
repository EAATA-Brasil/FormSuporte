from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponseBadRequest
from django.db.models import Q

from .models import SerialVCI, SerialFoto
from .forms import SerialVCIForm

# websocket broadcast
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


def broadcast_update():
    """Envia aviso para TODOS os usuários atualizarem a tabela."""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "serial_vci_updates",
        {
            "type": "enviar_update",
            "content": {"mensagem": "atualizar_tabela"}
        }
    )


def lista_seriais(request):
    """Página inicial + busca ajax."""
    query = request.GET.get("q", "")

    seriais = SerialVCI.objects.all().order_by("-id")

    if query:
        seriais = seriais.filter(
            Q(numero_vci__icontains=query) |
            Q(numero_tablet__icontains=query) |
            Q(numero_prog__icontains=query) |
            Q(cliente__icontains=query) |
            Q(email__icontains=query) |
            Q(telefone__icontains=query) |
            Q(pedido__icontains=query)
        )

    paginator = Paginator(seriais, 10)
    page = request.GET.get("page")
    seriais_page = paginator.get_page(page)

    # requisição AJAX → devolve só a tabela
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render(request, "serial_vci/_tabela.html", {
            "seriais": seriais_page,
            "query": query,
        })

    # requisição normal → página completa
    return render(request, "serial_vci/index.html", {
        "seriais": seriais_page,
        "query": query,
    })


def detalhes_serial(request, serial_id):
    serial = get_object_or_404(SerialVCI, id=serial_id)
    fotos = serial.fotos.all()

    return JsonResponse({
        "id": serial.id,
        "numero_vci": serial.numero_vci,
        "numero_tablet": serial.numero_tablet,
        "numero_prog": serial.numero_prog,
        "cliente": serial.cliente,
        "email": serial.email,
        "telefone": serial.telefone,
        "pedido": serial.pedido,
        "fotos": [f.imagem.url for f in fotos],
    })


def adicionar_serial(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Método inválido")

    form = SerialVCIForm(request.POST, request.FILES)

    if not form.is_valid():
        return JsonResponse({"success": False, "errors": form.errors})

    serial = form.save()

    # salvar múltiplas imagens
    fotos = request.FILES.getlist("fotos")
    for foto in fotos:
        SerialFoto.objects.create(serial=serial, imagem=foto)

    # broadcast realtime
    broadcast_update()

    return JsonResponse({"success": True})
