from django.apps import AppConfig

class OcorrenciaErroConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ocorrencia_erro'
    verbose_name = 'Ocorrência de erros'

    def ready(self):
        # Carrega signals
        import ocorrencia_erro.signals

        # Preenche métricas iniciais
        try:
            from .models import Record
            from .metrics import REGISTROS_EXISTENTES

            REGISTROS_EXISTENTES.set(Record.objects.count())

        except Exception as e:
            print(f"[METRICS INIT ERROR] {e}")
