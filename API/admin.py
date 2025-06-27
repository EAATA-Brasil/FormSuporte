from django.contrib import admin
from .models import Equipamentos, TipoEquipamento, MarcaEquipamento
from django import forms
import re

class EquipamentoForm(forms.ModelForm):
    class Meta:
        model = Equipamentos
        fields = '__all__'
        widgets = {
            'detalhes': forms.Textarea(attrs={
                'style': 'height: 200px; width: 80%;',
                'placeholder': 'Use *negrito*, _itálico_, ~tachado~, `código`'
            }),
        }

@admin.register(TipoEquipamento)
class GrupoEquipamentoAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)

@admin.register(MarcaEquipamento)
class MarcaEquipamentoAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)

@admin.register(Equipamentos)
class EquipamentoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'marca', 'grupo', 'disponibilidade')
    list_filter = ('grupo__nome', 'disponibilidade', 'marca__nome')
    search_fields = ('nome', 'marca__nome', 'grupo__nome')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'marca', 'grupo', 'disponibilidade')
        }),
        ('Valores', {
            'fields': ('custo', 'custo_geral', 'custo_cnpj', 'custo_cpf')
        }),
        ('Detalhes', {
            'fields': ('detalhes', 'detalhes_html'),
            'description': 'Use formatação WhatsApp: *negrito*, _itálico_, ~tachado~, `código`'
        }),
    )
    
    readonly_fields = ('detalhes_html',)