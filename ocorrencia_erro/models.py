from django.db import models
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.models import User

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


class Record(models.Model):
    class STATUS_OCORRENCIA(models.TextChoices):
        DONE = "DONE", "Concluído"
        LATE = "LATE", "Atrasado"
        PROGRESS = "PROGRESS", "Em progresso"
        REQUESTED = "REQUESTED", "Requisitado"

    # Campos de data
    data = models.DateField(
        verbose_name='Data de reporte', 
        default=timezone.now,  # Usando a referência da função, não a chamada
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

    # Campos de responsáveis
    technical = models.CharField(
        max_length=100, 
        default="Não identificado", 
        verbose_name='Técnico'
    )
    responsible = models.CharField(
        max_length=100, 
        default="Não identificado", 
        verbose_name='Responsável'
    )

    # Campos do equipamento
    device = models.ForeignKey(
        Device, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name='Equipamento'
    )
    area = models.CharField(
        max_length=20, 
        default="N/A", 
        verbose_name='Área',
        
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

    # Campos adicionais
    year = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        default='N/A', 
        verbose_name='Ano'
    )
    country = models.ForeignKey(
        Country, 
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

    # Campos de descrição
    problem_detected = models.TextField(
        default="Não identificado", 
        verbose_name="Problema detectado"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_OCORRENCIA.choices, 
        default=STATUS_OCORRENCIA.REQUESTED
    )

    # Feedbacks
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
        """Validações e ajustes automáticos dos dados"""
        super().clean()

        today = timezone.now().date()

        # Ajustes baseados no status
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

        # Validações de data
        if self.finished:
            if self.data and self.finished < self.data:
                raise ValidationError({
                    "finished": "Data de conclusão não pode ser anterior à data de reporte."
                })
            if self.deadline and self.finished < self.deadline:
                raise ValidationError({
                    "finished": "Data de conclusão não pode ser anterior ao prazo."
                })

        # Atualização automática do status
        if self.deadline and not self.finished:
            if (self.deadline - today).days < 0:
                self.status = self.STATUS_OCORRENCIA.LATE
            elif self.status == self.STATUS_OCORRENCIA.REQUESTED:
                self.status = self.STATUS_OCORRENCIA.PROGRESS

    def save(self, *args, **kwargs):
        """Garante que as validações sejam executadas antes de salvar"""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Ocorrência #{self.pk or 'Nova'} - {self.device} ({self.get_status_display()})"

    class Meta:
        verbose_name = "Ocorrência"
        verbose_name_plural = "Ocorrências"
        ordering = ["-data"]
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['device']),
            models.Index(fields=['data']),
        ]