from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Record, CountryPermission, Country, Device

# Admin para Record
@admin.register(Record)
class RecordAdmin(admin.ModelAdmin):
    list_display = ('status', 'data', 'responsible', 'device', 'country')
    search_fields = ('responsible', 'device__name', 'country__name')  # Buscando por nome do país
    list_filter = ('status','responsible', 'country__name')
    

# Inline para mostrar os países associados ao usuário
class CountryPermissionInline(admin.TabularInline):
    model = CountryPermission
    extra = 0
    verbose_name = "País de responsabilidade"
    verbose_name_plural = "Países de responsabilidade"

# Customizando o UserAdmin
class CustomUserAdmin(BaseUserAdmin):
    inlines = [CountryPermissionInline]

    def countries_responsible(self, obj):
        return ", ".join([p.country.name for p in obj.country_permissions.all()])

    countries_responsible.short_description = "Países Responsáveis"

    list_display = BaseUserAdmin.list_display + ('countries_responsible',)

# Re-registrando o User
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Opcional: admin para Country (pra facilitar adicionar países via admin)
@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    verbose_name = "País de responsabilidade"
    verbose_name_plural = "Países de responsabilidade"

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
