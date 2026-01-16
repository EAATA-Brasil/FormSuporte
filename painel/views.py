from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.utils.text import slugify
import random


def home(request):
	"""Painel gerencial: login simples e, se autenticado, links rápidos."""
	if request.method == 'POST':
		username = request.POST.get('username', '').strip()
		password = request.POST.get('password', '')
		user = authenticate(request, username=username, password=password)
		if user is not None:
			login(request, user)
			return redirect('painel_home')
		messages.error(request, 'Usuário ou senha inválidos.')

	if request.user.is_authenticated:
		return redirect('painel_dashboard')
	return render(request, 'painel/index.html')


def sair(request):
	logout(request)
	return redirect('painel_home')


def dashboard(request):
	"""Página principal após login, com atalhos para os módulos."""
	quick_links = [
		{"label": "Ocorrências", "href": "/ocorrencia/"},
		{"label": "Situação (Serial)", "href": "/situacao/"},
		{"label": "Simulador", "href": "/simulador/"},
		{"label": "Seriais VCI", "href": "/seriais/"},
		{"label": "Form (Veículos)", "href": "/form/"},
		{"label": "Pedidos", "href": "/pedido/"},
	]
	return render(request, 'painel/dashboard.html', {"quick_links": quick_links})


# Removido: pages() unificado ao dashboard


def settings_view(request):
	"""Configurações de conta: alterar senha (e espaço para futuras configs)."""
	if request.method == 'POST':
		form = PasswordChangeForm(request.user, request.POST)
		if form.is_valid():
			user = form.save()
			update_session_auth_hash(request, user)  # mantém a sessão ativa
			messages.success(request, 'Senha alterada com sucesso!')
			return redirect('painel_settings')
		else:
			messages.error(request, 'Verifique os erros abaixo.')
	else:
		form = PasswordChangeForm(request.user)

	return render(request, 'painel/settings.html', { 'form': form })


def user_create(request):
	"""Cadastro de usuário com hierarquia e área.
	Regras:
	- Superuser ou (dono/diretor/ti): cria qualquer papel, área opcional p/ dono/diretor.
	- Gestor: só cria COLABORADOR e a área é SEMPRE a área do gestor (forçado no backend).
	- Colaborador: não pode acessar.
	"""
	from django.conf import settings
	from .models import UserProfile

	profile = getattr(request.user, 'painel_profile', None)
	role_me = getattr(profile, 'role', None)
	setor_me = getattr(profile, 'setor', None)
	is_gestor = bool(role_me == 'gestor' and setor_me)
	is_master = bool(request.user.is_superuser or (role_me in ('dono', 'diretor', 'ti')))

	if not (is_master or is_gestor):
		return redirect('painel_dashboard')

	ROLE_CHOICES_ALL = [
		('dono', 'Dono'),
		('diretor', 'Diretor'),
		('gestor', 'Gestor'),
		('colaborador', 'Colaborador')
	]
	SETOR_CHOICES_ALL = [
        ('marketing', 'Marketing'),
        ('financeiro', 'Financeiro'),
        ('suporte', 'Suporte'),
        ('ti', 'TI'),
        ('comercial', 'Comercial')
    ]

	# Context inicial
	context = {}

	# Gestor: só cria colaborador e sempre na própria área
	if is_gestor:
		# mantém rótulo da área bonitinho
		area_label_map = dict(SETOR_CHOICES_ALL)
		context['roles'] = [('colaborador', 'Colaborador')]
		context['setores'] = [(setor_me, dict(SETOR_CHOICES_ALL).get(setor_me))]
		# flags opcionais p/ você travar o UI no template, se quiser
		context['force_role'] = 'colaborador'
		context['force_area'] = setor_me

		# ✅ Países aparecem só para gestor do SUPORTE (form legado)
		if setor_me == 'suporte':
			from ocorrencia_erro.models import Country
			context['paises'] = Country.objects.all().order_by('name')

	else:
		context['roles'] = ROLE_CHOICES_ALL
		context['setores'] = SETOR_CHOICES_ALL

	if request.method == 'POST':
		nome = (request.POST.get('nome') or '').strip()
		email = (request.POST.get('email') or '').strip() or None
		senha = (request.POST.get('senha') or '').strip()
		cpf_cnpj = (request.POST.get('cpf_cnpj') or '').strip()
		contato = (request.POST.get('contato') or '').strip()

		# 🔒 Força regra do gestor (ignora POST)
		if is_gestor:
			role = 'colaborador'
			setor = setor_me
		else:
			role = request.POST.get('role')
			setor = request.POST.get('setor')

		if not nome or not senha:
			context['error'] = 'Nome e senha são obrigatórios.'
			return render(request, 'painel/user_create.html', context)

		# Gera username
		base_username = (email.split('@')[0] if email else slugify(nome)) or 'user'
		username = base_username
		while User.objects.filter(username=username).exists():
			username = f"{base_username}{random.randint(10,99)}"

		user = User.objects.create_user(username=username, email=email, password=senha)
		user.first_name = nome

		# 🔒 Flags de admin
		if role in ('dono', 'diretor', 'ti'):
			user.is_staff = True
			user.is_superuser = True
		elif role == 'gestor':
			user.is_staff = True
			user.is_superuser = False
		else:
			# colaborador (inclui o criado por gestor)
			user.is_staff = False
			user.is_superuser = False

		user.save()

		# Garante grupo
		try:
			group, _ = Group.objects.get_or_create(name=role.capitalize())
			user.groups.add(group)
		except Exception:
			pass

		# Área no perfil:
		# - dono/diretor: área opcional (None)
		# - gestor/colaborador: área obrigatória (gestor já veio forçado)
		if role in ('dono', 'diretor'):
			setor_value = None
		else:
			if not setor:
				context['error'] = 'Selecione o setor para Gestor ou Colaborador.'
				return render(request, 'painel/user_create.html', context)
			setor_value = setor

		UserProfile.objects.create(
			user=user,
			role=role,
			setor=setor_value,
			cpf_cnpj=cpf_cnpj,
			contato=contato
		)

		# Se for GESTOR (criado por master), concede permissões (view/add/change/delete)
		# de todos os models dos apps que pertencem ao setor conforme settings.PAINEL_MODULE_AREAS
		if role == 'gestor' and setor_value:
			mapping = getattr(settings, 'PAINEL_MODULE_AREAS', {})
			app_labels = [app for app, a in mapping.items() if a == setor_value]
			if app_labels:
				perms = Permission.objects.filter(content_type__app_label__in=app_labels)
				user.user_permissions.add(*list(perms))

		messages.success(request, 'Usuário criado com sucesso!')
		return redirect('painel_dashboard')

	return render(request, 'painel/user_create.html', context)
