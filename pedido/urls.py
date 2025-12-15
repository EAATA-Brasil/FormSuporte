from django.urls import path
from . import views

app_name = "pedido"

urlpatterns = [
    path("novo/", views.criar_pedido, name="novo"),
    path("feito/", views.pedido_feito, name="pedido_feito"),
]
