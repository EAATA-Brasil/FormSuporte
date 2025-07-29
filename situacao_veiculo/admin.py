from django.contrib import admin
from .models import Cliente

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('serial', 'nome', 'equipamento', 'data', 'vencimento', 'anos_para_vencimento')
    search_fields = ('serial', 'nome', 'equipamento')
    list_editable = ('anos_para_vencimento',)  # Permite editar diretamente na lista
    fieldsets = (
        (None, {
            'fields': ('nome', 'data', 'anos_para_vencimento', 'vencimento'),
        }),
        ('Detalhes', {
            'fields': ('serial', 'cnpj', 'tel', 'equipamento'),
        }),
    )