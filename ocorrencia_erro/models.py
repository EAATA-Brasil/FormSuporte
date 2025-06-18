from django.db import models
from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.models import User

class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class CountryPermission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='country_permissions')
    country = models.ForeignKey(Country, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} - {self.country.name}"

def default_deadline():
    return timezone.now().date() + relativedelta(months=+5)

class Record(models.Model):
    class STATUS_OCORRENCIA(models.TextChoices):
        DONE = "DONE", "Concluído"
        LATE = "LATE", "Atrasado"
        PROGRESS = "PROGRESS", "Em progresso"
        REQUESTED = "REQUESTED", "Requisitado"

    data = models.DateField(verbose_name='Data de reporte', default=timezone.now().date)
    deadline = models.DateField(blank=True, null=True, verbose_name='Prazo')
    finished = models.DateField(blank=True, null=True, verbose_name='Concluído em')

    technical = models.CharField(max_length=100, default="Não identificado", verbose_name='Técnico')
    responsible = models.CharField(max_length=100, default="Não identificado", verbose_name='Responsável')

    device = models.CharField(max_length=100, default="N/A", verbose_name='Equipamento')
    area = models.CharField(max_length=20, default="N/A", verbose_name='Área')
    serial = models.CharField(max_length=20, blank=True, null=True, default="N/A", verbose_name='Serial')
    brand = models.CharField(max_length=100, blank=True, null=True, default="N/A", verbose_name='Marca')
    model = models.CharField(max_length=100, blank=True, null=True, default="N/A", verbose_name='Modelo')

    year = models.CharField(max_length=100, blank=True, null=True, default='N/A', verbose_name='Ano')
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='País', help_text="País")
    version = models.CharField(max_length=100, blank=True, null=True, default="N/A", verbose_name='Versão')

    problem_detected = models.TextField(default="Não identificado", verbose_name="Problema detectado")
    status = models.CharField(choices=STATUS_OCORRENCIA.choices, default=STATUS_OCORRENCIA.REQUESTED, max_length=20)

    feedback_technical = models.TextField(blank=True, null=True, default="Não identificado", verbose_name="Feedback Técnico")
    feedback_manager = models.TextField(blank=True, null=True, default="Não identificado", verbose_name="Feedback Manager")

    def clean(self):
        super().clean()

        today = timezone.now().date()

        # Se status for DONE mas finished estiver vazio, preenche com hoje
        if self.status == self.STATUS_OCORRENCIA.DONE and not self.finished:
            self.finished = today

        # Se finished foi preenchido mas status não é DONE, força o status para DONE
        elif self.finished and self.status != self.STATUS_OCORRENCIA.DONE:
            self.status = self.STATUS_OCORRENCIA.DONE

        # Se o status não for DONE mas finished estiver preenchido, limpa o finished
        elif self.status != self.STATUS_OCORRENCIA.DONE and self.finished:
            self.finished = None

        # Validação: finished não pode ser antes da data de reporte
        if self.finished and self.data and self.finished < self.data:
            raise ValidationError({"finished": "A data de conclusão não pode ser anterior à data de reporte."})

        # Validação: finished não pode ser antes da deadline
        if self.finished and self.deadline and self.finished < self.deadline:
            raise ValidationError({"finished": "A data de conclusão não pode ser anterior à data de prazo."})

        # Ajusta o status se houver deadline e ainda não tiver finished
        if self.deadline:
            if not self.finished and (self.deadline - today).days < 0:
                self.status = self.STATUS_OCORRENCIA.LATE
            elif not self.status or self.status == self.STATUS_OCORRENCIA.REQUESTED:
                self.status = self.STATUS_OCORRENCIA.PROGRESS

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Ocorrência #{self.pk or 'Nova'} - {self.device or 'N/A'} ({self.get_status_display()})"

    class Meta:
        verbose_name = "Ocorrência"
        verbose_name_plural = "Ocorrências"
        ordering = ["-data"]
