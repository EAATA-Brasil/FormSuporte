from django.db import models
import re
from django.utils.html import format_html, escape

class TipoEquipamento(models.Model):
    nome = models.CharField(
        max_length=100,
        help_text='Tipo do equipamento (diagnóstico, imobilizador, etc)',
        verbose_name='Tipo do equipamento'
    )

    def __str__(self):
        return self.nome

class MarcaEquipamento(models.Model):
    nome = models.CharField(verbose_name='Marca do equipamento', max_length=30)

    def __str__(self):
        return self.nome

class Equipamentos(models.Model):
    nome = models.CharField(verbose_name='Nome do equipamento', max_length=100)

    marca = models.ForeignKey(
        MarcaEquipamento,
        on_delete=models.CASCADE,
        related_name='equipamentos',
        verbose_name='Marca do equipamento'
    )

    grupo = models.ForeignKey(
        TipoEquipamento,
        on_delete=models.CASCADE,
        related_name='equipamentos',
        verbose_name='Tipo do equipamento'
    )

    custo = models.FloatField(verbose_name='Custo do equipamento')
    custo_geral = models.FloatField(verbose_name='Valor do equipamento dentro de SP')
    custo_cnpj = models.FloatField(verbose_name='Valor do equipamento para CNPJ fora de SP')
    custo_cpf = models.FloatField(verbose_name='Valor do equipamento para CPF fora de SP')

    entrada_sp_cnpj = models.FloatField(verbose_name='Entrada para São Paulo com CNPJ (padrão)', blank=True, null=True)
    entrada_outros_cnpj = models.FloatField(verbose_name='Entrada para outros estados com CNPJ (padrão)', blank=True, null=True)
    entrada_outros_cpf = models.FloatField(verbose_name='Entrada para outros estados com CPF (padrão)', blank=True, null=True)
    parcelas = models.FloatField(verbose_name='Quantidade de parcelas padrão', blank=True, null=True)

    disponibilidade = models.BooleanField(default=True, verbose_name='Equipamento disponível')

    detalhes = models.TextField(verbose_name='Detalhes do equipamento', blank=True, null=True)
    detalhes_html = models.TextField(verbose_name='Detalhes em HTML', editable=False, blank=True, null=True)

    detalhes_sp = models.TextField(verbose_name='Detalhes do equipamento (SP)', blank=True, null=True)
    detalhes_sp_html = models.TextField(verbose_name='Detalhes SP em HTML', editable=False, blank=True, null=True)

    def __str__(self):
        return f'{self.nome} - {self.marca} - {self.grupo}'

    def save(self, *args, **kwargs):
        """Converte os textos estilo WhatsApp em HTML formatado"""
        if self.detalhes:
            self.detalhes_html = self._convert_whatsapp_to_html(self.detalhes)
        else:
            self.detalhes_html = None

        if self.detalhes_sp:
            self.detalhes_sp_html = self._convert_whatsapp_to_html(self.detalhes_sp)
        else:
            self.detalhes_sp_html = None

        super().save(*args, **kwargs)

    def formatted_detalhes(self):
        """Mostra os detalhes formatados no admin"""
        return format_html(self.detalhes_html) if self.detalhes_html else ""
    formatted_detalhes.short_description = 'Detalhes Formatados'

    def formatted_detalhes_sp(self):
        """Mostra os detalhes SP formatados no admin"""
        return format_html(self.detalhes_sp_html) if self.detalhes_sp_html else ""
    formatted_detalhes_sp.short_description = 'Detalhes SP Formatados'

    @staticmethod
    def _convert_whatsapp_to_html(text):
        """Converte formatação WhatsApp para HTML"""
        if not text:
            return ""

        text = escape(text)

        # URLs → links clicáveis
        text = re.sub(
            r'(https?://\S+)',
            r'<a href="\1" target="_blank" rel="noopener noreferrer">\1</a>',
            text
        )

        # WhatsApp style → HTML tags
        text = re.sub(r'\*(.*?)\*', r'<strong>\1</strong>', text)  # negrito
        text = re.sub(r'_(.*?)_', r'<em>\1</em>', text)            # itálico
        text = re.sub(r'~(.*?)~', r'<strike>\1</strike>', text)    # tachado
        text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)        # monoespaçado

        # Linhas com "-" → lista
        text = re.sub(
            r'^- (.*)$',
            r'<li>\1</li>',
            text,
            flags=re.MULTILINE
        )

        if '<li>' in text:
            text = text.replace('<li>', '<ul><li>', 1)
            text += '</li></ul>'

        # Quebras de linha
        text = text.replace('\n', '<br>')

        return text