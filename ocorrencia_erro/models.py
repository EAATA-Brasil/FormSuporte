# ocorrencia/models.py

from django.db import models
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.models import User
import uuid
import random
import string

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

def gerar_codigo_espanha():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

class Record(models.Model):
    def is_awaiting_china_late(self):
        return self.status == self.STATUS_OCORRENCIA.AWAITING_CHINA and self.deadline and self.deadline < timezone.now().date()
    
    class STATUS_OCORRENCIA(models.TextChoices):
        DONE = "DONE", "Concluído"
        LATE = "LATE", "Atrasado"
        PROGRESS = "PROGRESS", "Em progresso"
        REQUESTED = "REQUESTED", "Requisitado"
        AWAITING_CHINA = "AWAITING_CHINA", "Aguardando China"
        AWAITING_CHINA_LATE = "AWAITING_CHINA_LATE", "China Atrasada"

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
        Device,
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
    contact = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        default="N/A",
        verbose_name='Contato'
    )
    vin = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        default="N/A",
        verbose_name='VIN'
    )
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
    tipo_ecu = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Tipo de ECU'
    )
    tipo_motor = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Tipo de Motor'
    )
    sistema = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name='Sistema'
    )
    tipo_problema = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name='Tipo de Problema'
    )
    # FIXED: Removed on_delete from CharField
    country_original = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='País inicial'
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
        max_length=25,
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
    detalhes_responsavel = models.TextField(
        blank=True,
        null=True,
        default="Não identificado",
        verbose_name="Detalhes do Responsável"
    )
    tipo_chave = models.TextField(
        blank=True,
        null=True,
        default="Não identificado",
        verbose_name="Tipo Chave"
    )

    # Em seu arquivo models.py, dentro da classe Record
    def clear_finished_date(self):
        """Método para limpar explicitamente a data de finished"""
        self.finished = None
        self._explicitly_cleared_finished = True  # Flag para evitar auto-preencher
        if self.status == self.STATUS_OCORRENCIA.DONE:
            self.status = self.STATUS_OCORRENCIA.PROGRESS
    def clear_deadline_date(self):
        """Método para limpar explicitamente a data de finished"""
        self.deadline= None
        self._explicitly_cleared_deadline = True  # Flag para evitar auto-preencher
        if self.status != self.STATUS_OCORRENCIA.AWAITING_CHINA:
            self.status = self.STATUS_OCORRENCIA.REQUESTED
            
    def clean(self):
        """
        Validações e lógica de status com a ordem de prioridade correta.
        """
        super().clean()
        today = timezone.now().date()
        # =====================================================
        # 0. PRIORIDADE ABSOLUTA — FINALIZADO → DONE
        # =====================================================
        if self.finished:
            self.status = self.STATUS_OCORRENCIA.DONE
            return  # Nada mais pode sobrescrever
            

        # =====================================================
        # 1. STATUS CHINA TEM PRIORIDADE (desde que não esteja finalizado)
        # =====================================================
        if self.status in [self.STATUS_OCORRENCIA.AWAITING_CHINA, self.STATUS_OCORRENCIA.AWAITING_CHINA_LATE]:
            # Se o prazo existe e já passou, o status DEVE ser AWAITING_CHINA_LATE.
            if self.deadline and self.deadline < today:
                self.status = self.STATUS_OCORRENCIA.AWAITING_CHINA_LATE
            # Caso contrário (se não há prazo ou o prazo está no futuro), deve ser AWAITING_CHINA.
            else:
                self.status = self.STATUS_OCORRENCIA.AWAITING_CHINA
            # Retornamos para garantir que a lógica de status geral abaixo não seja executada e não sobrescreva a nossa decisão.
            return

        # 2. LÓGICA DE STATUS GERAL (só é executada se o status não for relacionado à China)
        if self.finished and self.status != self.STATUS_OCORRENCIA.DONE:
            self.status = self.STATUS_OCORRENCIA.DONE
        elif self.status != self.STATUS_OCORRENCIA.DONE and self.finished:
            self.finished = None

        if not self.finished:
            if self.deadline:
                # Esta verificação agora não interfere mais com os status da China.
                if (self.deadline - today).days < 0:
                    if self.status != self.STATUS_OCORRENCIA.DONE:
                        self.status = self.STATUS_OCORRENCIA.LATE
                elif self.status == self.STATUS_OCORRENCIA.REQUESTED:
                    self.status = self.STATUS_OCORRENCIA.PROGRESS
            elif self.status not in [self.STATUS_OCORRENCIA.PROGRESS, self.STATUS_OCORRENCIA.DONE]:
                self.status = self.STATUS_OCORRENCIA.REQUESTED

        self.area = self.area.upper() if self.area else ''
        self.brand = self.brand.upper() if self.brand else ''
        self.model = self.model.upper() if self.model else ''
        self.technical = self.technical.capitalize() if self.technical else ''

    # O método save() não precisa de alterações.
    def save(self, *args, **kwargs):
        if not self.country_original and self.country:
            self.country_original = self.country.name
        
        self.clean()
        
        super().save(*args, **kwargs)

        if not self.codigo_externo and 'codigo_externo' not in (kwargs.get('update_fields') or []):
            self.codigo_externo = str(self.id)
            super().save(update_fields=['codigo_externo'])

class ArquivoOcorrencia(models.Model):
    record = models.ForeignKey(Record, on_delete=models.CASCADE, related_name='arquivos', null=True)
    arquivo = models.FileField(upload_to='download_arquivo/')
    nome_original = models.CharField(max_length=255, blank=True)
    data_upload = models.DateTimeField(verbose_name="Data de upload", default=timezone.now)

    def __str__(self):
        return f"{self.record} salve {self.arquivo}"


class Notificacao(models.Model):
    """
    Modelo para notificações de feedback em ocorrências
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='notificacoes',
        verbose_name='Usuário'
    )
    record = models.ForeignKey(
        Record, 
        on_delete=models.CASCADE, 
        related_name='notificacoes',
        verbose_name='Ocorrência'
    )
    tipo = models.CharField(
        max_length=20,
        choices=[
            ('feedback_manager', 'Feedback do Gestor'),
        ],
        default='feedback_manager',
        verbose_name='Tipo de Notificação'
    )
    titulo = models.CharField(
        max_length=200,
        verbose_name='Título'
    )
    resumo = models.TextField(
        max_length=500,
        verbose_name='Resumo'
    )
    lida = models.BooleanField(
        default=False,
        verbose_name='Lida'
    )
    criada_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criada em'
    )
    lida_em = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Lida em'
    )

    class Meta:
        verbose_name = "Notificação"
        verbose_name_plural = "Notificações"
        ordering = ['-criada_em']
        indexes = [
            models.Index(fields=['user', 'lida']),
            models.Index(fields=['criada_em']),
        ]

    def __str__(self):
        return f"Notificação para {self.user.username} - {self.titulo}"

    def marcar_como_lida(self):
        """Marca a notificação como lida"""
        if not self.lida:
            self.delete()
            # self.lida = True
            # self.lida_em = timezone.now()
            # self.save(update_fields=['lida', 'lida_em'])

class ChatMessage(models.Model):
    record = models.ForeignKey(Record, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField(blank=True)
    image_base64 = models.TextField(blank=True, null=True)  # Para armazenar Base64
    image_type = models.CharField(max_length=50, blank=True, null=True)
    image_name = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']


class OptionItem(models.Model):
    """Opções configuráveis para Sistema e Tipo de Problema por Área (IMMO/Diagnosis/Device)."""
    AREA_CHOICES = (
        ('IMMO', 'IMMO'),
        ('Diagnosis', 'Diagnosis'),
        ('Device', 'Device'),
    )
    CATEGORY_CHOICES = (
        ('SISTEMA', 'Sistema'),
        ('PROBLEMA', 'Tipo de Problema'),
    )

    area = models.CharField(max_length=20, choices=AREA_CHOICES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    label = models.CharField(max_length=150)
    order = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Quando category == 'PROBLEMA', liga ao item de SISTEMA correspondente
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')

    class Meta:
        unique_together = ('area', 'category', 'label', 'parent')
        ordering = ['category', 'area', 'parent__label', 'order', 'label']

    def __str__(self) -> str:
        return f"{self.get_category_display()} / {self.area} - {self.label}"
