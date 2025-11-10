from django.db import models
import re
from django.utils.html import format_html, escape

class TipoEquipamento(models.Model):
    """
    Modelo para categorizar os equipamentos (ex: Diagnóstico, Imobilizador).
    """
    nome = models.CharField(
        max_length=100,
        help_text='Tipo do equipamento (diagnóstico, imobilizador, etc)',
        verbose_name='Tipo do equipamento'
    )

    class Meta:
        verbose_name = "Tipo de Equipamento"
        verbose_name_plural = "Tipos de Equipamento"

    def __str__(self):
        """Retorna o nome do tipo de equipamento."""
        return self.nome

class MarcaEquipamento(models.Model):
    """
    Modelo para registrar as marcas dos equipamentos.
    """
    nome = models.CharField(verbose_name='Marca do equipamento', max_length=30)

    class Meta:
        verbose_name = "Marca de Equipamento"
        verbose_name_plural = "Marcas de Equipamento"

    def __str__(self):
        """Retorna o nome da marca."""
        return self.nome

class Equipamentos(models.Model):
    """
    Modelo principal para armazenar dados de equipamentos, custos e detalhes
    para simulação de vendas.
    """
    # --- Campos de Identificação ---
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

    # --- Campos de Custo e Preço ---
    custo = models.FloatField(
        verbose_name='Custo do equipamento (interno)', 
        blank=True, 
        null=True
    )
    custo_geral = models.FloatField(
        verbose_name='Valor do equipamento dentro de SP (Preço de Venda)'
    )
    custo_cnpj = models.FloatField(
        verbose_name='Valor do equipamento para CNPJ fora de SP (Preço de Venda)'
    )
    custo_cpf = models.FloatField(
        verbose_name='Valor do equipamento para CPF fora de SP (Preço de Venda)'
    )

    # --- Campos de Condições de Pagamento Padrão ---
    entrada_sp_cnpj = models.FloatField(
        verbose_name='Entrada para São Paulo com CNPJ (padrão)', 
        blank=True, 
        null=True
    )
    entrada_outros_cnpj = models.FloatField(
        verbose_name='Entrada para outros estados com CNPJ (padrão)', 
        blank=True, 
        null=True
    )
    entrada_outros_cpf = models.FloatField(
        verbose_name='Entrada para outros estados com CPF (padrão)', 
        blank=True, 
        null=True
    )
    parcelas = models.FloatField(
        verbose_name='Quantidade de parcelas padrão', 
        blank=True, 
        null=True
    )

    # --- Novo: valor opcional de cartão 12x ---
    valor_cartao_12x = models.FloatField(
        verbose_name='Valor da parcela no cartão (12x)',
        blank=True,
        null=True
    )

    # --- Campos de Status e Regras de Venda ---
    disponibilidade = models.BooleanField(
        default=True, 
        verbose_name='Equipamento disponível'
    )
    avista = models.BooleanField(
        default=False, 
        verbose_name='Venda sozinha apenas à vista'
    )
    boleto = models.BooleanField(
        default=True, 
        verbose_name='Aceita parcelar no boleto'
    )

    # --- Campos de Detalhes e Formatação ---
    detalhes = models.TextField(
        verbose_name='Detalhes do equipamento (formato WhatsApp)', 
        blank=True, 
        null=True
    )
    detalhes_html = models.TextField(
        verbose_name='Detalhes em HTML (Gerado Automaticamente)', 
        editable=False, 
        blank=True, 
        null=True
    )

    detalhes_sp = models.TextField(
        verbose_name='Detalhes do equipamento (SP - formato WhatsApp)', 
        blank=True, 
        null=True
    )
    detalhes_sp_html = models.TextField(
        verbose_name='Detalhes SP em HTML (Gerado Automaticamente)', 
        editable=False, 
        blank=True, 
        null=True
    )

    class Meta:
        verbose_name = "Equipamento"
        verbose_name_plural = "Equipamentos"

    def __str__(self):
        """Retorna uma representação em string do equipamento."""
        return f'{self.nome} - {self.marca} - {self.grupo}'

    def save(self, *args, **kwargs):
        """
        Sobrescreve o método save para converter automaticamente os campos
        'detalhes' e 'detalhes_sp' de formato WhatsApp para HTML.
        Também aplica regras automáticas para os campos 'avista' e 'boleto'
        com base nas condições de pagamento recebidas.
        """
        # ------ Regras avista / boleto ------
        parcelas_boleto = self.parcelas if self.parcelas is not None else 0
        valor_cartao_12x = self.valor_cartao_12x if self.valor_cartao_12x is not None else 0

        # Se cartão 12x não é relevante (None ou < 2) E boleto também não parcela (None ou < 2) -> somente à vista
        if valor_cartao_12x < 2 and parcelas_boleto < 2:
            self.avista = True
        else:
            self.avista = False

        # Se tem 2 ou mais parcelas no boleto -> aceita boleto parcelado
        self.boleto = parcelas_boleto > 1

        # ------ Conversão de detalhes para HTML ------
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
        """
        Propriedade para exibir os detalhes formatados em HTML no painel Admin.
        """
        return format_html(self.detalhes_html) if self.detalhes_html else ""
    formatted_detalhes.short_description = 'Detalhes Formatados'

    def formatted_detalhes_sp(self):
        """
        Propriedade para exibir os detalhes SP formatados em HTML no painel Admin.
        """
        return format_html(self.detalhes_sp_html) if self.detalhes_sp_html else ""
    formatted_detalhes_sp.short_description = 'Detalhes SP Formatados'

    @staticmethod
    def _convert_whatsapp_to_html(text):
        """
        Função estática para converter formatação de texto estilo WhatsApp
        (negrito, itálico, tachado, lista) para tags HTML.
        """
        if not text:
            return ""

        # 1. Escapa caracteres HTML para evitar XSS
        text = escape(text)

        # 2. URLs → links clicáveis
        text = re.sub(
            r'(https?://\S+)',
            r'<a href="\1" target="_blank" rel="noopener noreferrer">\1</a>',
            text
        )

        # 3. Formatação WhatsApp → Tags HTML
        text = re.sub(r'\*(.*?)\*', r'<strong>\1</strong>', text)  # negrito (*texto*)
        text = re.sub(r'_(.*?)_', r'<em>\1</em>', text)            # itálico (_texto_)
        text = re.sub(r'~(.*?)~', r'<strike>\1</strike>', text)    # tachado (~texto~)
        text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)        # monoespaçado (`texto`)

        # 4. Linhas com "-" → Lista (<li>)
        # Converte linhas que começam com "- " em itens de lista <li>
        text = re.sub(
            r'^- (.*)$',
            r'<li>\1</li>',
            text,
            flags=re.MULTILINE
        )

        # 5. Envolve a lista em tags <ul>
        if '<li>' in text:
            # Adiciona <ul> no início da primeira <li>
            text = text.replace('<li>', '<ul><li>', 1)
            # Adiciona </ul> no final
            text += '</ul>'

        # 6. Quebras de linha (\n) → <br>
        text = text.replace('\n', '<br>')

        return text