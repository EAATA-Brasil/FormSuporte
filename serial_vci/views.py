from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponseBadRequest
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt

from .forms import SerialVCIForm, SerialVCIEditForm 
from .models import (
    SerialVCI,
    SerialFoto,
    Garantia,
    GarantiaFoto,
    GarantiaComentario,
    GarantiaComentarioFoto
)

from .metrics import (
    SERIAL_CADASTRADO, SERIAL_EDITADO, FOTO_ADICIONADA, FOTO_REMOVIDA,
    GARANTIA_CRIADA, GARANTIA_DELETADA,
    COMENTARIO_CRIADO, COMENTARIO_DELETADO,
    TOTAL_SERIAIS, TOTAL_GARANTIAS, TOTAL_COMENTARIOS
)


# websocket broadcast
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .metrics import SERIAL_CADASTRADO

def executar_simulacao(request):
    SERIAL_CADASTRADO.inc()

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
    serial = get_object_or_404(SerialVCI, id=serial_id)
    
    garantias = []
    for g in serial.garantias.all().order_by("-id"):

        comentarios = []
        for c in g.comentarios.all().order_by("id"):
            comentarios.append({
                "id": c.id,
                "texto": c.texto,
                "criado_em": c.criado_em.strftime("%d/%m/%Y %H:%M"),
                "fotos": [f.imagem.url for f in c.fotos.all()]
            })

        garantias.append({
            "id": g.id,
            "titulo": g.titulo,
            "descricao": g.descricao,
            "criado_em": g.criado_em.strftime("%d/%m/%Y %H:%M"),
            "fotos": [f.imagem.url for f in g.fotos.all()],
            "comentarios": comentarios         #  <<< AGORA EXISTE!!
        })

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
        "fotos": [f.imagem.url for f in serial.fotos.all()],
        "fotos_edicao": [
            {"id": f.id, "url": f.imagem.url}
            for f in serial.fotos.all()
        ],
        "garantias": garantias,
        "is_superuser": request.user.is_superuser,

    })


def adicionar_serial(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Método inválido")

    form = SerialVCIForm(request.POST, request.FILES)

    if not form.is_valid():
        return JsonResponse({"success": False, "errors": form.errors})

    serial = form.save()

    SERIAL_CADASTRADO.inc()
    TOTAL_SERIAIS.set(SerialVCI.objects.count())

    # Salvar fotos
    fotos = request.FILES.getlist("fotos")
    for foto in fotos:
        SerialFoto.objects.create(serial=serial, imagem=foto)
        FOTO_ADICIONADA.inc()

    broadcast_update()

    return JsonResponse({"success": True})

def editar_serial(request, serial_id):

    if request.method != "POST":
        return HttpResponseBadRequest("Método inválido")

    serial = get_object_or_404(SerialVCI, id=serial_id)

    form = SerialVCIEditForm(request.POST, request.FILES, instance=serial)

    if not form.is_valid():
        return JsonResponse({"success": False, "errors": form.errors})

    form.save()

    SERIAL_EDITADO.inc()

    # adicionar novas fotos
    for foto in request.FILES.getlist("fotos"):
        SerialFoto.objects.create(serial=serial, imagem=foto)
        FOTO_ADICIONADA.inc()

    broadcast_update()

    return JsonResponse({"success": True})


def remover_foto(request, foto_id):

    if request.method != "POST":
        return JsonResponse({"success": False}, status=400)

    foto = get_object_or_404(SerialFoto, id=foto_id)
    
    foto.imagem.delete(save=False)
    foto.delete()

    FOTO_REMOVIDA.inc()

    broadcast_update()

    return JsonResponse({"success": True})
   

@csrf_exempt
def add_garantia(request, serial_id):

    if request.method != "POST":
        return JsonResponse({"error": "Método inválido"}, status=400)

    serial = get_object_or_404(SerialVCI, id=serial_id)

    garantia = Garantia.objects.create(
        serial=serial,
        titulo=request.POST.get("titulo", ""),
        descricao=request.POST.get("descricao", "")
    )

    GARANTIA_CRIADA.inc()
    TOTAL_GARANTIAS.set(Garantia.objects.count())

    for foto in request.FILES.getlist("fotos"):
        GarantiaFoto.objects.create(garantia=garantia, imagem=foto)
        FOTO_ADICIONADA.inc()

    return JsonResponse({"success": True})


def garantia_detalhes(request, garantia_id):
    garantia = get_object_or_404(Garantia, id=garantia_id)

    comentarios = []
    for c in garantia.comentarios.all().order_by("id"):
        comentarios.append({
            "id": c.id,
            "texto": c.texto,
            "criado_em": c.criado_em.strftime("%d/%m/%Y %H:%M"),
            "fotos": [f.imagem.url for f in c.fotos.all()]
        })

    return JsonResponse({
        "id": garantia.id,
        "titulo": garantia.titulo,
        "comentarios": comentarios
    })

@csrf_exempt
def add_comentario(request, garantia_id):

    if request.method != "POST":
        return JsonResponse({"error": "Método inválido"}, status=400)

    garantia = get_object_or_404(Garantia, id=garantia_id)

    comentario = GarantiaComentario.objects.create(
        garantia=garantia,
        texto=request.POST.get("texto", "")
    )

    COMENTARIO_CRIADO.inc()
    TOTAL_COMENTARIOS.set(GarantiaComentario.objects.count())

    for foto in request.FILES.getlist("fotos"):
        GarantiaComentarioFoto.objects.create(
            comentario=comentario,
            imagem=foto
        )
        FOTO_ADICIONADA.inc()

    return JsonResponse({"success": True})


@csrf_exempt
def deletar_garantia(request, garantia_id):

    if request.method != "POST":
        return JsonResponse({"error": "Método inválido"}, status=400)

    garantia = get_object_or_404(Garantia, id=garantia_id)

    # deletar fotos e comentários normalmente
    for comentario in garantia.comentarios.all():
        for foto in comentario.fotos.all():
            foto.imagem.delete(save=False)
            foto.delete()
        comentario.delete()
        COMENTARIO_DELETADO.inc()

    for foto in garantia.fotos.all():
        foto.imagem.delete(save=False)
        foto.delete()

    garantia.delete()

    GARANTIA_DELETADA.inc()
    TOTAL_GARANTIAS.set(Garantia.objects.count())
    TOTAL_COMENTARIOS.set(GarantiaComentario.objects.count())

    return JsonResponse({"success": True})


@csrf_exempt
def delete_comentario(request, comentario_id):

    comentario = get_object_or_404(GarantiaComentario, id=comentario_id)

    for foto in comentario.fotos.all():
        foto.imagem.delete(save=False)
        foto.delete()

    comentario.delete()

    COMENTARIO_DELETADO.inc()
    TOTAL_COMENTARIOS.set(GarantiaComentario.objects.count())

    return JsonResponse({"success": True})

