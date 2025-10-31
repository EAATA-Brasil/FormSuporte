from django.db import models
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import date

class Cliente(models.Model):
    data = models.DateField(verbose_name="Data", blank=False, default=timezone.now)
    vencimento = models.DateField(verbose_name="Vencimento", blank=True, null=True)
    anos_para_vencimento = models.PositiveIntegerField(
        verbose_name="Anos para vencimento",
        default=2,
        help_text="Quantidade de anos até o vencimento."
    )
    serial = models.CharField(verbose_name="Serial", max_length=100, blank=True)
    nome = models.CharField(verbose_name="Nome", max_length=100, blank=True, null=True)
    cnpj = models.CharField(max_length=30, verbose_name='CPF/CNPJ', blank=True, default="SEM DADO", null=True)
    tel = models.CharField(max_length=30, verbose_name='Telefone', blank=True, default="SEM DADO", null=True)
    equipamento = models.CharField(verbose_name='Equipamento', max_length=100, blank=True, default="", null=True)

    status_message_custom = models.CharField(
        "Mensagem de status (curta) - personalizada",
        max_length=200,
        blank=True,
        null=True,
        help_text="Se preenchido, sobrescreve a mensagem padrão (ex.: 'SUPORTE LIBERADO', 'SUPORTE LIBERADO')."
    )

    # Mantém o campo de texto detalhado
    mensagem = models.TextField(
        "Mensagem (detalhada)",
        blank=True,
        null=True,
        help_text="Mensagem descritiva exibida quando existir."
    )

    updated_at = models.DateTimeField(
        "Atualizado em",
        auto_now=True,
        help_text="Data/hora da última atualização deste cadastro."
    )

    def has_custom_message(self):
        return bool(self.status_message_custom or self.mensagem)
    has_custom_message.boolean = True
    has_custom_message.short_description = "Msg personalizada?"

    def clean(self):
        if self.serial:
            qs = Cliente.objects.filter(serial=self.serial)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError({'serial': 'Este serial já está cadastrado para outro cliente.'})

    def save(self, *args, **kwargs):
        if not self.vencimento and self.data and self.anos_para_vencimento:
            self.vencimento = self.data + relativedelta(years=self.anos_para_vencimento)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nome} - {self.vencimento}"

    @property
    def _vencimento_dias(self):
        if not self.vencimento:
            return -999999
        return (self.vencimento - date.today()).days

    @property
    def status(self):
        if not self.vencimento:
            return 'indefinido'
        if self.vencimento < self.data:
            return 'bloqueado_data_invalida'
        dias = self._vencimento_dias
        if dias > 30:
            return 'direito'
        elif dias < 1:
            return 'vencido'
        else:
            return 'vencendo'

    # Mensagem padrão calculada pelo status
    @property
    def status_message_default(self):
        s = self.status
        if s == 'direito':
            return "SUPORTE LIBERADO - Atender normalmente"
        elif s == 'vencido':
            return "SUPORTE VENCIDO - Não fazer atendimento - BLOQUEADO"
        elif s == 'vencendo':
            return "SUPORTE A VENCER - Atender normalmente - Passar para o comercial"
        elif s == 'bloqueado_data_invalida':
            return "Não fazer atendimento - INFORMAR AO GESTOR"
        else:
            return "Consultar ativação - ATUALIZAR DADOS."

    # ✅ Mensagem EFETIVA (preferir custom; senão, padrão)
    @property
    def status_message(self):
        return self.status_message_custom or self.status_message_default
