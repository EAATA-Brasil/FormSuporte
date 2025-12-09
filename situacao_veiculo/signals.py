from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from situacao_veiculo.models import Cliente
from serial_vci.models import SerialVCI

# ---- IMPORTAR MÉTRICAS ----
from .metrics import (
    CLIENTES_EXISTENTES,
    CADASTRO_SUCESSO as CADASTRO_CRIADO,
)


# ==========================================================
# 1) MÉTRICAS AUTOMÁTICAS — Cliente criado / removido
# ==========================================================

@receiver(post_save, sender=Cliente)
def atualizar_metricas_cliente(sender, instance, created, **kwargs):
    """Atualiza métricas sempre que um Cliente é criado ou alterado."""
    if created:
        CADASTRO_CRIADO.inc()

    CLIENTES_EXISTENTES.set(Cliente.objects.count())


@receiver(post_delete, sender=Cliente)
def atualizar_metricas_delete(sender, instance, **kwargs):
    CLIENTES_EXISTENTES.set(Cliente.objects.count())


# ==========================================================
# 2) SINCRONIZAÇÃO Cliente → SerialVCI
# ==========================================================

@receiver(post_save, sender=Cliente)
def sincronizar_serial(sender, instance, **kwargs):

    serial, created = SerialVCI.objects.get_or_create(
        numero_vci=instance.serial,
        defaults={
            "data": instance.data,
            "cliente": instance.nome,
            "telefone": instance.tel,
            "email": "",
            "pedido": "",
            "numero_tablet": "",
            "numero_prog": "",
        }
    )

    if not created:
        serial.cliente = instance.nome
        serial.telefone = instance.tel
        serial.data = instance.data
        serial.save()
