from django.contrib import admin
from .models import Equipamentos, TipoEquipamento, MarcaEquipamento

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
    list_display = ('nome', 'marca', 'grupo',)
    list_filter = ('grupo__nome', 'disponibilidade','marca__nome')
