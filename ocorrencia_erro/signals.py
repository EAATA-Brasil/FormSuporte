from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Record, ArquivoOcorrencia
from .metrics import (
    REGISTROS_CRIADOS,
    REGISTROS_ATUALIZADOS,
    ARQUIVOS_ENVIADOS,
    ARQUIVOS_BAIXADOS,
    TEMPO_RESOLUCAO,
    REGISTROS_EXISTENTES
)
from django.utils import timezone


# ---- OCORRÊNCIAS CRIADAS ----
@receiver(post_save, sender=Record)
def registrar_criacao(sender, instance, created, **kwargs):
    if created:
        REGISTROS_CRIADOS.inc()
    # atualiza Gauge
    REGISTROS_EXISTENTES.set(Record.objects.count())


# ---- OCORRÊNCIAS DELETADAS ----
@receiver(post_delete, sender=Record)
def registrar_delete(sender, instance, **kwargs):
    REGISTROS_EXISTENTES.set(Record.objects.count())


# ---- UPLOAD DE ARQUIVOS ----
@receiver(post_save, sender=ArquivoOcorrencia)
def arquivo_enviado(sender, instance, created, **kwargs):
    if created:
        ARQUIVOS_ENVIADOS.inc()


# ---- DOWNLOAD DE ARQUIVOS ----
# você incrementa isso na view do download:
# ARQUIVOS_BAIXADOS.inc()


# ---- TEMPO DE RESOLUÇÃO ----
@receiver(post_save, sender=Record)
def registrar_tempo_resolucao(sender, instance, **kwargs):
    if instance.finished:
        inicio = instance.criado_em.timestamp()
        fim = instance.finished.timestamp()
        TEMPO_RESOLUCAO.observe(fim - inicio)
