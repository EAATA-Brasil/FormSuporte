from django.contrib import admin
from .models import Record

@admin.register(Record)
class RecordAdmin(admin.ModelAdmin):
    list_display = ('status', 'data', 'responsible','device', 'country')
    search_fields = ('responsible','device','country')