from django.urls import path
from . import views

urlpatterns = [
    path("", views.lista_seriais, name="lista_seriais"),
    path("adicionar/", views.adicionar_serial, name="adicionar_serial"),
    path("detalhes/<int:serial_id>/", views.detalhes_serial, name="detalhes_serial"),
]
