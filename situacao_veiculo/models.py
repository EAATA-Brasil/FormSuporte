from django.db import models
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.core.exceptions import ValidationError

class Cliente(models.Model):
    data = models.DateField(verbose_name="Data", blank=False, default=timezone.now)
    vencimento = models.DateField(verbose_name="Vencimento", blank=True, null=True)
    anos_para_vencimento = models.PositiveIntegerField(
        verbose_name="Anos para vencimento",
        default=2,  # Valor padrão: 2 anos
        help_text="Quantidade de anos até o vencimento."
    )
    serial = models.CharField(verbose_name="Serial", max_length=100, blank=True, null=True)
    nome = models.CharField(verbose_name="Nome", max_length=100, blank=False)
    cnpj = models.CharField(max_length=30, verbose_name='CPF/CNPJ', blank=True, default="SEM DADO")
    tel = models.CharField(max_length=30, verbose_name='Telefone', blank=True, default="SEM DADO")
    equipamento = models.CharField(verbose_name='Equipamento', max_length=100, blank=True, default="")

    def clean(self):
        if self.serial:
            qs = Cliente.objects.filter(serial=self.serial)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError({'serial': 'Este serial já está cadastrado para outro cliente.'})

    def save(self, *args, **kwargs):
        self.clean()  # chama o clean para validar
        if not self.vencimento:
            if self.data and self.anos_para_vencimento:
                self.vencimento = self.data + relativedelta(years=self.anos_para_vencimento)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nome} - {self.vencimento}"