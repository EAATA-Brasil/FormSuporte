# urls.py (do seu app API ou simulador)
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'equipamentos', views.EquipamentosViewSet)
router.register(r'tipos-equipamento', views.TipoEquipamentoViewSet)
router.register(r'marcas-equipamento', views.MarcaEquipamentoViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('generate-pdf/', views.generate_pdf, name='generate_pdf'),
]