from django.apps import AppConfig
import threading


class SituacaoVeiculoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'situacao_veiculo'
    verbose_name = 'Verificar suporte'

    def ready(self):
        # Carrega sinais
        import situacao_veiculo.signals

        # IMPORTANTE: adiar execução até o servidor estar 100% carregado
        threading.Timer(1.0, self.carregar_metricas_passadas).start()

    def carregar_metricas_passadas(self):
        """
        Função executada 1 segundo após o Django iniciar,
        garantindo que o banco e apps estão prontos.
        """
        try:
            from situacao_veiculo.models import Cliente
            from .metrics import CLIENTES_EXISTENTES

            total = Cliente.objects.count()
            CLIENTES_EXISTENTES.set(total)

            print(f"[METRICS] Clientes carregados para Prometheus: {total}")

        except Exception as e:
            print(f"[METRICS] Erro ao carregar métricas históricas: {e}")
