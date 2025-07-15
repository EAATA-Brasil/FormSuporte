from django.contrib import admin
from .models import Cliente

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('serial', 'nome', 'vencimento')
    search_fields = ('serial','nome')