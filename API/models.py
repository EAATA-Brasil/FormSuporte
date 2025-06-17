from django.db import models

class TipoEquipamento(models.Model):
    nome=models.CharField(max_length=100, help_text='Tipo do equipamento(diagnóstico, imobilizador, etc)', verbose_name='Tipo do equipamento')

    def __str__(self):

        return self.nome

class MarcaEquipamento(models.Model):
    nome = models.CharField(verbose_name='Marca do equipamento',max_length=30)

    def __str__(self):

        return self.nome
    

class Equipamentos(models.Model):
    nome = models.CharField(verbose_name='Nome do equipamento', name='nome', max_length=100)  # ou qualquer valor adequado
    
    marca = models.ForeignKey(MarcaEquipamento, on_delete=models.CASCADE, related_name='equipamentos', verbose_name='Marca do equipamento', name='marca')
    grupo = models.ForeignKey(TipoEquipamento, on_delete=models.CASCADE, related_name='equipamentos', verbose_name='Tipo do equipamento', name='grupo')
    custo = models.FloatField(verbose_name='Custo do equipamento',name='custo')
    custo_geral = models.FloatField(verbose_name='Valor do equipamento dentro de SP',name='custo_geral')
    custo_cnpj = models.FloatField(verbose_name='Valor do equipamento para CNPJ fora de SP',name='custo_cnpj')
    custo_cpf = models.FloatField(verbose_name='Valor do equipamento para CPF fora de SP',name='custo_cpf')
    disponibilidade = models.BooleanField(verbose_name='Equipamento disponível', name='disponibilidade', default=True)

    def __str__(self):
        return f'{self.nome} - {self.marca} - {self.grupo}'
    