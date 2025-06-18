from django.db import models
from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.models import User

class CountryPermission(models.Model):
    """Define quais países cada usuário pode visualizar nas ocorrências."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='country_permissions')
    country = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.user.username} - {self.country.upper()}'

    class Meta:
        verbose_name = "Permissão de País"
        verbose_name_plural = "Permissões de Países"
        unique_together = ('user', 'country')
        
def default_deadline():
    """Retorna a data atual mais 5 meses como prazo padrão."""
    return timezone.now().date() + relativedelta(months=+5)

class Record(models.Model):
    """Modelo para registrar ocorrências."""

    class STATUS_OCORRENCIA(models.TextChoices):
        """Define os possíveis status de uma ocorrência."""
        DONE = "DONE", "Concluído"
        LATE = "LATE", "Atrasado"
        PROGRESS = "PROGRESS", "Em progresso"
        REQUESTED = "REQUESTED", "Requisitado"

    # Date fields
    data = models.DateField(verbose_name='Data de reporte', help_text="Data de reporte", default=timezone.now)
    deadline = models.DateField(blank=True,null=True, verbose_name='Prazo', help_text="Data de previsão para término")
    finished = models.DateField(blank=True, null=True, verbose_name='Concluído em', help_text="Data de previsão para término")

    # Technical information
    technical = models.CharField(blank=False,null=False, verbose_name='Técnico', help_text="Técnico que reportou", max_length=100, default="Não identificado")
    responsible = models.CharField(verbose_name='Responsável', help_text="Técnico responsável",max_length=100, default="Não identificado")

    # Equipment details
    device = models.CharField(blank=False,null=False, verbose_name='Equipamento',help_text="Equipamento",max_length=100, default="N/A")
    area = models.CharField(blank=False,null=False, verbose_name='Área',help_text="Área",max_length=20, default="N/A")
    serial = models.CharField(blank=True,null=True, verbose_name='Serial',help_text="Serial",max_length=20,default="N/A")
    brand = models.CharField(blank=True,null=True, verbose_name='Marca',help_text="Marca",max_length=100,default="N/A")
    model = models.CharField(blank=True,null=True, verbose_name='Modelo',help_text="Modelo",max_length=100,default="N/A")

    # Additional information
    year = models.CharField(blank=True,null=True, max_length=100,verbose_name='Ano',help_text="Ano",default='N/A')
    country = models.CharField(blank=True,null=True, verbose_name='País',help_text="País",max_length=100, default="Brasil")
    version = models.CharField(blank=True,null=True, verbose_name='Versão',help_text="Versão",max_length=100, default="N/A")

    # Problem tracking
    problem_detected = models.TextField(blank=False,null=False, verbose_name="Problema detectado",help_text="Problema detectado", default="Não identificado")
    status = models.CharField(choices=STATUS_OCORRENCIA.choices,default=STATUS_OCORRENCIA.REQUESTED,max_length=20)

    #Feedbacks 
    feedback_technical = models.TextField(blank=True,null=True,verbose_name="Feedback Técnico",help_text="Feedback Técnico", default="Não identificado")
    feedback_manager = models.TextField(blank=True,null=True,verbose_name="Feedback Manager", help_text="Feedback Manager", default="Não identificado")

    # --- Métodos ---
    def clean(self):
        """Aplica validações e lógicas automáticas antes de salvar."""
        super().clean() # Chama a validação padrão

        # 1. Garante data de conclusão se status for DONE
        if self.status == self.STATUS_OCORRENCIA.DONE and not self.finished:
            self.finished = timezone.now().date()
            # Opcional: Verificar se o feedback técnico foi preenchido
            # if not self.feedback_tecnico:
            #     raise ValidationError({"feedback_tecnico": "Feedback técnico é obrigatório ao concluir."})

        # 2. Garante status DONE se data de conclusão for preenchida
        elif self.finished and self.status != self.STATUS_OCORRENCIA.DONE:
            # Poderia lançar um erro ou ajustar automaticamente
            # raise ValidationError({"status": "Status deve ser 'Concluído' se a data de conclusão está preenchida."})
            self.status = self.STATUS_OCORRENCIA.DONE # Ajuste automático

        # 3. Limpa data de conclusão se status voltar a não ser DONE
        elif self.status != self.STATUS_OCORRENCIA.DONE and self.finished:
            self.finished = None

        # 4. Validação de Datas (Exemplo: Conclusão não pode ser antes do reporte)
        if self.finished and self.data and self.finished < self.data:
            raise ValidationError({
                "finished": "A data de conclusão não pode ser anterior à data de reporte."
            })
        if self.finished and self.deadline and self.finished < self.deadline:
            raise ValidationError({
                "finished": "A data de conclusão não pode ser anterior à data de prazo."
            })
        
        # 5. Status LATE se já tiver ultrapassado a deadline
        if self.deadline:
            if not self.finished and (self.deadline - timezone.now().date()).days < 0:
                self.status = self.STATUS_OCORRENCIA.LATE

        if self.deadline and (not self.status or self.status == self.STATUS_OCORRENCIA.REQUESTED):
            self.status = self.STATUS_OCORRENCIA.PROGRESS

        self.country = self.country.__str__().upper()

    def save(self, *args, **kwargs):
        """Sobrescreve o save para garantir que clean() seja chamado."""
        self.clean() # Chama as validações personalizadas
        super().save(*args, **kwargs) # Salva o objeto

    def __str__(self):
        """Representação textual do objeto Record."""
        return f"Ocorrência #{self.pk or 'Nova'} - {self.device or 'N/A'} ({self.get_status_display()})"

    class Meta:
        """Metadados para o modelo Record."""
        verbose_name = "Ocorrência"
        verbose_name_plural = "Ocorrências"
        ordering = ["-data"] # Ordenar pelas mais recentes primeiro por padrão
        # Adicionar índices se necessário para otimizar queries complexas
        # indexes = [
        #     models.Index(fields=["status", "prazo"]),
        # ]
