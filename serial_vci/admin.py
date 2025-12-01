from django.contrib import admin
from .models import SerialVCI, SerialFoto

class FotosInline(admin.TabularInline):
    model = SerialFoto
    extra = 1

@admin.register(SerialVCI)
class SerialVCIAdmin(admin.ModelAdmin):
    list_display = ("numero_vci", "cliente", "email", "pedido")
    inlines = [FotosInline]

admin.site.register(SerialFoto)
