from django.contrib import admin
from .models import Cliente
from django.db.models import Count, Subquery, OuterRef, Exists
from django.urls import reverse
from django.utils.html import format_html

class SerialDuplicadoFilter(admin.SimpleListFilter):
    title = 'Serial duplicado'
    parameter_name = 'serial_duplicado'

    def lookups(self, request, model_admin):
        return (
            ('sim', 'Duplicados'),
            ('nao', 'Não duplicados'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'sim':
            # Serial que aparece mais de uma vez
            duplicados = (Cliente.objects
                          .values('serial')
                          .annotate(serial_count=Count('id'))
                          .filter(serial_count__gt=1)
                          .values('serial'))
            return queryset.filter(serial__in=duplicados)
        elif self.value() == 'nao':
            duplicados = (Cliente.objects
                          .values('serial')
                          .annotate(serial_count=Count('id'))
                          .filter(serial_count__gt=1)
                          .values('serial'))
            return queryset.exclude(serial__in=duplicados)
        return queryset
    

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('serial', 'nome', 'equipamento', 'data', 'vencimento', 'anos_para_vencimento', 'acoes')
    search_fields = ('serial', 'nome', 'equipamento')
    list_filter = (SerialDuplicadoFilter,)
    list_editable = ('anos_para_vencimento',)  # Permite editar diretamente na lista
    fieldsets = (
        (None, {
            'fields': ('nome', 'data', 'anos_para_vencimento', 'vencimento'),
        }),
        ('Detalhes', {
            'fields': ('serial', 'cnpj', 'tel', 'equipamento'),
        }),
    )
    def acoes(self, obj):
        url = reverse('admin:situacao_veiculo_cliente_delete', args=[obj.pk])
        return format_html('<a class="button" href="{}">Excluir</a>', url)
    acoes.short_description = 'Excluir'
    acoes.allow_tags = True