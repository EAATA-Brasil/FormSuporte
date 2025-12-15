from django.shortcuts import render, redirect
from .models import Pedido
from .forms import PedidoForm, PedidoItemFormSet

def criar_pedido(request):
    if request.method == "POST":
        form = PedidoForm(request.POST)
        formset = PedidoItemFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            pedido = form.save()
            itens = formset.save(commit=False)

            total = 0
            for item in itens:
                item.pedido = pedido
                item.save()
                total += item.total

            pedido.total_geral = total
            pedido.save()

            return redirect("pedido_feito")

    else:
        form = PedidoForm()
        formset = PedidoItemFormSet()

    return render(request, "pedido/pedido_form.html", {
        "form": form,
        "formset": formset
    })


def pedido_feito(request):
    return render(request, "pedido/pedido_feito.html")
