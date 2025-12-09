from django.apps import AppConfig

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'API'

    def ready(self):
        from .models import Equipamentos, TipoEquipamento, MarcaEquipamento
        from .metrics import TOTAL_EQUIPAMENTOS, TOTAL_TIPOS, TOTAL_MARCAS

        TOTAL_EQUIPAMENTOS.set(Equipamentos.objects.count())
        TOTAL_TIPOS.set(TipoEquipamento.objects.count())
        TOTAL_MARCAS.set(MarcaEquipamento.objects.count())
