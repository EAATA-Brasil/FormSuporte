from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
	class Role(models.TextChoices):
		DONO = 'dono', 'Dono'
		DIRETOR = 'diretor', 'Diretor'
		GESTOR = 'gestor', 'Gestor'
		COLABORADOR = 'colaborador', 'Colaborador'

	class Setor(models.TextChoices):
		MARKETING = 'marketing', 'Marketing'
		FINANCEIRO = 'financeiro', 'Financeiro'
		SUPORTE = 'suporte', 'Suporte'
		TI = 'ti', 'TI'
		COMERCIAL = 'comercial', 'Comercial'

	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='painel_profile')

	role = models.CharField(max_length=20, choices=Role.choices)

	# 🔄 era "area", agora é SETOR
	setor = models.CharField(max_length=20, choices=Setor.choices, blank=True, null=True)

	# 🆕 NOVO CAMPO (filtro de responsabilidade)
	area = models.CharField(max_length=100, blank=True, null=True)

	cpf_cnpj = models.CharField(max_length=30, blank=True, null=True)
	contato = models.CharField(max_length=100, blank=True, null=True)

	def __str__(self):
		return f"{self.user.username} ({self.get_role_display()})"
