from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponseBadRequest
from django.db.models import Q

from .models import SerialVCI, SerialFoto
# Importar ambos os formulários
from .forms import SerialVCIForm, SerialVCIEditForm 

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
    page_number = request.GET.get("page", 1) 

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
    seriais_page = paginator.get_page(page_number) 

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
    """Retorna detalhes (e dados de edição) para pop-ups."""
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
        "data": serial.data.strftime("%d/%m/%Y") if serial.data else None,
        # URLs de fotos para exibição no modal de Detalhes
        "fotos": [f.imagem.url for f in fotos],
        # Dados de foto (ID e URL) para o modal de Edição (NOVO)
        "fotos_edicao": [{"id": f.id, "url": f.imagem.url} for f in fotos],
    })


def adicionar_serial(request):
    """View para adicionar novo serial."""
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

    broadcast_update()

    return JsonResponse({"success": True})


def editar_serial(request, serial_id):
    """View para editar SerialVCI (restrito aos campos VCI, Tablet, Prog e Fotos)."""
    if request.method != "POST":
        return HttpResponseBadRequest("Método inválido")

    serial = get_object_or_404(SerialVCI, id=serial_id)
    
    # Usa o SerialVCIEditForm que contém apenas os campos VCI, Tablet e Prog
    form = SerialVCIEditForm(request.POST, request.FILES, instance=serial)

    if not form.is_valid():
        return JsonResponse({"success": False, "errors": form.errors})

    # Salva apenas os campos VCI, Tablet, Prog 
    serial = form.save()

    # Adicionar novas imagens
    fotos = request.FILES.getlist("fotos")
    for foto in fotos:
        SerialFoto.objects.create(serial=serial, imagem=foto)

    broadcast_update()

    return JsonResponse({"success": True})


def remover_foto(request, foto_id):
    """View para remover uma foto existente (usada no modal de edição)."""
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Método inválido"}, status=400)

    try:
        foto = get_object_or_404(SerialFoto, id=foto_id)
        # Remove o arquivo físico e do DB
        foto.imagem.delete(save=False) 
        foto.delete()
        
        broadcast_update()
        
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)