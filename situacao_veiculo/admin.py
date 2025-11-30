# situacao_veiculo/admin.py
from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html
from django.utils import timezone
from django.utils import formats  # ⬅️ para formatar respeitando locale
from django.db import models
from django.forms import Textarea

from .models import Cliente

class SerialDuplicadoFilter(admin.SimpleListFilter):
    title = 'Serial duplicado'
    parameter_name = 'serial_duplicado'
    def lookups(self, request, model_admin):
        return (('sim', 'Duplicados'), ('nao', 'Não duplicados'))
    def queryset(self, request, queryset):
        duplicados = (
            Cliente.objects.values('serial')
            .annotate(serial_count=Count('id'))
            .filter(serial_count__gt=1)
            .values('serial')
        )
        if self.value() == 'sim':
            return queryset.filter(serial__in=duplicados)
        elif self.value() == 'nao':
            return queryset.exclude(serial__in=duplicados)
        return queryset

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = (
        'serial', 'nome', 'equipamento', 'data', 'vencimento',
        'anos_para_vencimento',
        'atualizado_mes','acoes'
    )
    search_fields = ('serial', 'nome', 'equipamento', 'status_message_custom', 'mensagem')
    list_filter = (SerialDuplicadoFilter,)
    list_editable = ('anos_para_vencimento',)

    fieldsets = (
        (None, {
            'fields': ('nome', 'data', 'anos_para_vencimento', 'vencimento'),
        }),
        ('Detalhes', {
            'fields': ('serial', 'cnpj', 'tel', 'equipamento'),
        }),
        ('Mensagens (opcional)', {
            'classes': ('collapse',),
            'fields': ('status_message_custom', 'mensagem'),
            'description': "Se vazio, usa a mensagem padrão calculada pelo status."
        }),
        ('Auditoria', {
            'fields': ('updated_at',),  # ⬅️ aparece completo aqui
        }),
    )

    readonly_fields = ('updated_at',)  # ⬅️ para não editar manualmente

    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 5, 'style': 'width: 100%'})},
    }

    def acoes(self, obj):
        url = reverse('admin:situacao_veiculo_cliente_delete', args=[obj.pk])
        return format_html('<a class="button" href="{}">Excluir</a>', url)
    acoes.short_description = 'Excluir'
    acoes.allow_tags = True

    @admin.display(description='Atualização (mês)')
    def atualizado_mes(self, obj):
        if not obj.updated_at:
            return "-"
        # Converte para timezone atual e formata "F Y" (ex.: "outubro 2025") conforme locale
        dt = timezone.localtime(obj.updated_at)
        return formats.date_format(dt, "F Y")
