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
    class STATUS_OCORRENCIA(models.TextChoices):
        DONE = "DONE", "Concluído"
        LATE = "LATE", "Atrasado"
        PROGRESS = "PROGRESS", "Em progresso"
        REQUESTED = "REQUESTED", "Requisitado"
        AWAITING = "AWAITING", "Aguardando"

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

    # Em seu arquivo models.py, dentro da classe Record
    def clear_finished_date(self):
        """Método para limpar explicitamente a data de finished"""
        self.finished = None
        self._explicitly_cleared_finished = True  # Flag para evitar auto-preencher
        if self.status == self.STATUS_OCORRENCIA.DONE:
            self.status = self.STATUS_OCORRENCIA.PROGRESS
    def clean(self):
        """
        Validações e lógica de status normal (quando o país NÃO é China).
        """
        super().clean()

        # Se o país for China, a lógica de status será tratada no save(), então pulamos o resto.
        if self.country and self.country.name == 'China':
            return

        today = timezone.now().date()

        if self.finished and self.status != self.STATUS_OCORRENCIA.DONE:
            self.status = self.STATUS_OCORRENCIA.DONE
        elif self.status != self.STATUS_OCORRENCIA.DONE and self.finished:
            self.finished = None

        if not self.finished:
            if self.deadline:
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

    def save(self, *args, **kwargs):
        """
        Garante a ordem correta de execução e a prioridade da regra da China.
        """
        # 1. Armazena o país original se ainda não foi definido
        if not self.country_original and self.country:
            self.country_original = self.country.name
        
        # 2. Chama clean() para validações
        self.clean()

        # 3. REGRA DA CHINA (PRIORIDADE MÁXIMA): Sobrescreve qualquer status anterior
        if self.country and self.country.name == 'China':
            self.status = self.STATUS_OCORRENCIA.AWAITING
        
        # 4. Salva o registro
        super().save(*args, **kwargs)

        # 5. Lógica para gerar código externo (apenas para novos registros)
        if not self.codigo_externo and 'codigo_externo' not in (kwargs.get('update_fields') or []):
            self.codigo_externo = str(self.id)
            super().save(update_fields=['codigo_externo'])

class ArquivoOcorrencia(models.Model):
    record = models.ForeignKey(Record, on_delete=models.CASCADE, related_name='arquivos', null=True)
    arquivo = models.FileField(upload_to='download_arquivo/')
    nome_original = models.CharField(max_length=255, blank=True)

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
            self.lida = True
            self.lida_em = timezone.now()
            self.save(update_fields=['lida', 'lida_em'])

class ChatMessage(models.Model):
    # FIXED: Removed invalid app reference from ForeignKey
    record = models.ForeignKey(Record, on_delete=models.CASCADE, related_name='chat_messages')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']