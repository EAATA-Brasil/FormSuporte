# Em seu_app/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Country, CountryPermission

@receiver(post_save, sender=User)
def grant_china_permission(sender, instance, created, **kwargs):
    """
    Este sinal é acionado sempre que um usuário é salvo.
    Ele garante que o usuário tenha permissão para a China.
    """
    try:
        # 1. Busca ou cria o país "China" para garantir que ele exista.
        #    O `get_or_create` é seguro e evita erros se o país já existir.
        china_country, country_created = Country.objects.get_or_create(name='China')
        
        # 2. Verifica se o usuário já tem a permissão para a China.
        #    O `update_or_create` é a forma mais eficiente e segura de fazer isso.
        #    Ele cria a permissão se não existir e não faz nada se já existir.
        CountryPermission.objects.update_or_create(
            user=instance,
            country=china_country,
            defaults={} # Não precisamos atualizar nenhum campo, apenas garantir a existência.
        )
        
        # Opcional: Log para saber quando a permissão foi verificada/criada.
        # if created:
        #     print(f"Permissão da China garantida para o novo usuário: {instance.username}")
        # else:
        #     print(f"Verificada permissão da China para o usuário existente: {instance.username}")

    except Exception as e:
        # É uma boa prática registrar qualquer erro que possa ocorrer no processo.
        print(f"ERRO ao tentar conceder permissão da China para {instance.username}: {e}")

