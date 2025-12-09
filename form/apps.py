from django.apps import AppConfig

class FormConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'form'
    verbose_name = 'Formulário chaveiros'

    def ready(self):
        from .models import Veiculo
        from .metrics import VEICULOS_EXISTENTES
        VEICULOS_EXISTENTES.set(Veiculo.objects.count())
