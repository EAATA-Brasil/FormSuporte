from django.contrib import admin
from django import forms
from .models import Equipamentos, MarcaEquipamento, TipoEquipamento

# Formulário personalizado para estilizar campos longos
class EquipamentoForm(forms.ModelForm):
    class Meta:
        model = Equipamentos
        fields = '__all__'
        widgets = {
            'detalhes': forms.Textarea(attrs={
                'style': 'height: 200px; width: 80%;',
                'placeholder': 'Use *negrito*, _itálico_, ~tachado~, `código`'
            }),
            'detalhes_sp': forms.Textarea(attrs={
                'style': 'height: 200px; width: 80%;',
                'placeholder': 'Use *negrito*, _itálico_, ~tachado~, `código`'
            }),
        }

# Registro do modelo Equipamentos com personalização completa
@admin.register(Equipamentos)
class EquipamentoAdmin(admin.ModelAdmin):
    form = EquipamentoForm

    list_display = ('nome', 'marca', 'grupo', 'disponibilidade')
    list_filter = ('grupo__nome', 'disponibilidade', 'marca__nome')
    search_fields = ('nome', 'marca__nome', 'grupo__nome')

    readonly_fields = ('detalhes_html', 'detalhes_sp_html')

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'marca', 'grupo', 'disponibilidade')
        }),
        ('Configurações', {
            'fields': ('entrada_sp_cnpj', 'entrada_outros_cnpj', 'entrada_outros_cpf', 'parcelas')
        }),
        ('Valores', {
            'fields': ('custo', 'custo_geral', 'custo_cnpj', 'custo_cpf')
        }),
        ('Detalhes Gerais', {
            'fields': ('detalhes', 'detalhes_html'),
            'description': 'Use *negrito*, _itálico_, ~tachado~, `código`, ou links completos (https://...)'
        }),
        ('Detalhes SP', {
            'fields': ('detalhes_sp', 'detalhes_sp_html'),
            'description': 'Versão alternativa para São Paulo. Mesmo formato do campo anterior.'
        }),
    )

# Registro auxiliar (sem customização, apenas visibilidade no admin)
@admin.register(MarcaEquipamento)
class MarcaEquipamentoAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)

@admin.register(TipoEquipamento)
class TipoEquipamentoAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)
