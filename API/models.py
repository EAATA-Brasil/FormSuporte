from django.db import models
import re
from django.utils.html import format_html, escape
from django.utils.safestring import mark_safe

class TipoEquipamento(models.Model):
    nome = models.CharField(max_length=100, 
                          help_text='Tipo do equipamento(diagnóstico, imobilizador, etc)', 
                          verbose_name='Tipo do equipamento')

    def __str__(self):
        return self.nome

class MarcaEquipamento(models.Model):
    nome = models.CharField(verbose_name='Marca do equipamento', max_length=30)

    def __str__(self):
        return self.nome

class Equipamentos(models.Model):
    nome = models.CharField(verbose_name='Nome do equipamento', max_length=100)
    marca = models.ForeignKey(MarcaEquipamento, on_delete=models.CASCADE, 
                            related_name='equipamentos', 
                            verbose_name='Marca do equipamento')
    grupo = models.ForeignKey(TipoEquipamento, on_delete=models.CASCADE, 
                            related_name='equipamentos', 
                            verbose_name='Tipo do equipamento')
    custo = models.FloatField(verbose_name='Custo do equipamento')
    custo_geral = models.FloatField(verbose_name='Valor do equipamento dentro de SP')
    custo_cnpj = models.FloatField(verbose_name='Valor do equipamento para CNPJ fora de SP')
    custo_cpf = models.FloatField(verbose_name='Valor do equipamento para CPF fora de SP')
    disponibilidade = models.BooleanField(verbose_name='Equipamento disponível', default=True)
    detalhes = models.TextField(verbose_name='Detalhes do equipamento', blank=True, null=True)
    detalhes_html = models.TextField(verbose_name='Detalhes em HTML', editable=False, blank=True, null=True)

    def __str__(self):
        return f'{self.nome} - {self.marca} - {self.grupo}'

    def save(self, *args, **kwargs):
        """Saves the HTML converted version of the WhatsApp formatted text"""
        if self.detalhes:
            self.detalhes_html = self._convert_whatsapp_to_html(self.detalhes)
        super().save(*args, **kwargs)

    def formatted_detalhes(self):
        """Returns the formatted HTML for admin display"""
        return format_html(self.detalhes_html) if self.detalhes_html else ""
    formatted_detalhes.short_description = 'Detalhes Formatados'

    @staticmethod
    def _convert_whatsapp_to_html(text):
        """Converts WhatsApp formatting to HTML with proper URL and list handling"""
        if not text:
            return ""
            
        # First escape HTML to prevent XSS
        text = escape(text)
        
        # Convert URLs to links
        text = re.sub(
            r'(https?://\S+)', 
            r'<a href="\1" target="_blank" rel="noopener noreferrer">\1</a>', 
            text
        )
        
        # Convert WhatsApp formatting to HTML
        text = re.sub(r'\*(.*?)\*', r'<strong>\1</strong>', text)  # Bold
        text = re.sub(r'_(.*?)_', r'<em>\1</em>', text)  # Italic
        text = re.sub(r'~(.*?)~', r'<strike>\1</strike>', text)  # Strike
        text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)  # Monospace
        
        # Convert lines starting with - to list items
        text = re.sub(
            r'^- (.*)$', 
            r'<li>\1</li>', 
            text, 
            flags=re.MULTILINE
        )
        
        # Wrap list items in <ul> tags if we found any
        if '<li>' in text:
            text = text.replace('<li>', '<ul><li>', 1)
            text += '</ul>'
        
        # Convert line breaks to <br> tags
        text = text.replace('\n', '<br>')
        
        return text