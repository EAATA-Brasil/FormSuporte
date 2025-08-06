from django.db import models
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.models import User
import uuid

class Country(models.Model):
    class Meta:
        verbose_name = "País"
        verbose_name_plural = "Países"
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
    
class Device(models.Model):
    class Meta:
        verbose_name = "Equipamento"
        verbose_name_plural = "Equipamentos"
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name

class CountryPermission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='country_permissions')
    country = models.ForeignKey(Country, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} - {self.country.name}"

import random
import string
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

def gerar_codigo_espanha():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

class Record(models.Model):
    class STATUS_OCORRENCIA(models.TextChoices):
        DONE = "DONE", "Concluído"
        LATE = "LATE", "Atrasado"
        PROGRESS = "PROGRESS", "Em progresso"
        REQUESTED = "REQUESTED", "Requisitado"

    # ID padrão autoincremental
    id = models.AutoField(primary_key=True)

    # Novo campo código externo
    codigo_externo = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        unique=True
    )

    data = models.DateField(
        verbose_name='Data de reporte',
        default=timezone.now,
        help_text="Data em que o problema foi reportado"
    )
    deadline = models.DateField(
        verbose_name='Prazo',
        blank=True,
        null=True,
        help_text="Prazo para resolução do problema"
    )
    finished = models.DateField(
        verbose_name='Concluído em',
        blank=True,
        null=True,
        help_text="Data em que o problema foi resolvido"
    )

    arquivo = models.FileField(upload_to='uploads/', null=True, blank=True)

    technical = models.CharField(
        max_length=100,
        default="Não identificado",
        verbose_name='Técnico'
    )
    responsible = models.CharField(
        max_length=100,
        default="Não identificado",
        verbose_name='Responsável',
        null=True,
        blank=True
    )

    device = models.ForeignKey(
        'Device',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Equipamento'
    )
    area = models.CharField(
        max_length=20,
        default="N/A",
        verbose_name='Área'
    )
    serial = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        default="N/A",
        verbose_name='Serial'
    )
    brand = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        default="N/A",
        verbose_name='Marca'
    )
    model = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        default="N/A",
        verbose_name='Modelo'
    )
    year = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        default='N/A',
        verbose_name='Ano'
    )
    country = models.ForeignKey(
        'Country',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='País'
    )
    version = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        default="N/A",
        verbose_name='Versão'
    )

    problem_detected = models.TextField(
        default="Não identificado",
        verbose_name="Problema detectado"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_OCORRENCIA.choices,
        default=STATUS_OCORRENCIA.REQUESTED
    )

    feedback_technical = models.TextField(
        blank=True,
        null=True,
        default="Não identificado",
        verbose_name="Feedback Técnico"
    )
    feedback_manager = models.TextField(
        blank=True,
        null=True,
        default="Não identificado",
        verbose_name="Feedback Manager"
    )

    def clean(self):
        super().clean()

        today = timezone.now().date()

        if self.status == self.STATUS_OCORRENCIA.DONE and not self.finished:
            self.finished = today
        elif self.finished and self.status != self.STATUS_OCORRENCIA.DONE:
            self.status = self.STATUS_OCORRENCIA.DONE
        elif self.status != self.STATUS_OCORRENCIA.DONE and self.finished:
            self.finished = None

        self.area = self.area.upper() if self.area else ''
        self.brand = self.brand.upper() if self.brand else ''
        self.model = self.model.upper() if self.model else ''
        self.technical = self.technical.capitalize() if self.technical else ''

        if self.finished:
            if self.data and self.finished < self.data:
                raise ValidationError({
                    "finished": "Data de conclusão não pode ser anterior à data de reporte."
                })

        if self.deadline and not self.finished:
            if (self.deadline - today).days < 0:
                self.status = self.STATUS_OCORRENCIA.LATE
            elif self.status == self.STATUS_OCORRENCIA.REQUESTED:
                self.status = self.STATUS_OCORRENCIA.PROGRESS

    def save(self, *args, **kwargs):
        self.full_clean()

        super().save(*args, **kwargs)  # Salva para ter id

        if not self.codigo_externo:
            self.codigo_externo = str(self.id)
            super().save(update_fields=['codigo_externo'])

    def __str__(self):
        return f"Ocorrência #{self.codigo_externo or self.id} - {self.device} ({self.get_status_display()})"

    class Meta:
        verbose_name = "Ocorrência"
        verbose_name_plural = "Ocorrências"
        ordering = ["-data"]
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['device']),
            models.Index(fields=['data']),
        ]


class ArquivoOcorrencia(models.Model):
    record = models.ForeignKey('Record', on_delete=models.CASCADE, related_name='arquivos', null=True)
    arquivo = models.FileField(upload_to='download_arquivo/')
    nome_original = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.record} salve {self.arquivo}"
