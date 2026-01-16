from django.conf import settings


def painel_modules(request):
    # Fonte única de verdade: settings.PAINEL_MODULE_AREAS
    mapping = getattr(settings, 'PAINEL_MODULE_AREAS', {})

    # Nomes legíveis por app (fallback gera Title a partir do label)
    name_map = {
        'ocorrencia_erro': 'Ocorrências',
        'situacao_veiculo': 'Situação (Serial)',
        'simulador': 'Simulador',
        'serial_vci': 'Seriais VCI',
        'form': 'Form (Veículos)',
        'pedido': 'Pedidos',
        'API': 'API',
    }

    modules = []
    for app_label, setor in mapping.items():
        name = name_map.get(app_label, app_label.replace('_', ' ').title())
        url = f"/admin/{app_label}/"
        modules.append({"app": app_label, "name": name, "url": url, "setor": setor})

    role = None
    setor = None
    if getattr(request, 'user', None) and request.user.is_authenticated:
        profile = getattr(request.user, 'painel_profile', None)
        if profile:
            role = profile.role
            setor = profile.setor

    allowed = modules
    if not (getattr(request, 'user', None) and request.user.is_authenticated):
        allowed = []
    else:
        if request.user.is_superuser or (role in ('dono', 'diretor', 'ti')):
            allowed = modules
        elif role == 'gestor' and setor:
            allowed = [m for m in modules if m['setor'] == setor]
        else:
            allowed = []

    return {
        'admin_modules': modules,
        'allowed_admin_modules': allowed,
        'user_role': role,
        'user_setor': setor,
        'user_area': profile.area if profile else None,
        'PAINEL_MODULE_AREAS': getattr(settings, 'PAINEL_MODULE_AREAS', {}),
    }
