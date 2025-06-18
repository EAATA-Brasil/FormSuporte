from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Record, CountryPermission

# Admin para Record (mantendo o que você já tinha)
@admin.register(Record)
class RecordAdmin(admin.ModelAdmin):
    list_display = ('status', 'data', 'responsible', 'device', 'country')
    search_fields = ('responsible', 'device', 'country')

# Inline para listar e editar os países responsáveis dentro do admin de User
class CountryPermissionInline(admin.TabularInline):
    model = CountryPermission
    extra = 0
    verbose_name = "País de responsabilidade"
    verbose_name_plural = "Países de responsabilidade"

# Personalizando o UserAdmin
class CustomUserAdmin(BaseUserAdmin):
    inlines = [CountryPermissionInline]

    def countries_responsible(self, obj):
        return ", ".join([p.country for p in obj.country_permissions.all()])

    countries_responsible.short_description = "Países Responsáveis"

    # Exibir também os países na lista de usuários
    list_display = BaseUserAdmin.list_display + ('countries_responsible',)

# Re-registrando o User com o novo admin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
