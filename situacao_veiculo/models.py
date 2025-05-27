from django.db import models
from dateutil.relativedelta import relativedelta
from django.utils import timezone

class Cliente(models.Model):
    data = models.DateField(verbose_name="Data",blank=False, default=timezone.now)
    vencimento = models.DateField(verbose_name="Vencimento", blank=True, null=True)
    serial = models.CharField(verbose_name="Serial", max_length=100, blank=True, null=True)
    nome = models.CharField(verbose_name="Nome", max_length=100, blank=False)
    cnpj = models.CharField(max_length=30, verbose_name='CPF/CNPJ', blank=True, default="SEM DADO")
    tel = models.CharField(max_length=30, verbose_name='Telefone', blank=True, default="SEM DADO")
    equipamento = models.CharField(verbose_name='Equipamento', max_length=100, blank=True)

    def save(self, *args, **kwargs):
        if self.data and not self.vencimento:
            self.vencimento = self.data + relativedelta(years=2)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nome} - {self.vencimento}"