# Generated by Django 5.2.1 on 2025-06-04 13:59

import datetime
import ocorrencia_erro.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ocorrencia_erro', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='record',
            name='area',
            field=models.CharField(default='N/A', help_text='Área', max_length=20, verbose_name='Área'),
        ),
        migrations.AddField(
            model_name='record',
            name='brand',
            field=models.CharField(blank=True, default='N/A', help_text='Marca', max_length=100, null=True, verbose_name='Marca'),
        ),
        migrations.AddField(
            model_name='record',
            name='country',
            field=models.CharField(blank=True, default='Brasil', help_text='País', max_length=100, null=True, verbose_name='País'),
        ),
        migrations.AddField(
            model_name='record',
            name='deadline',
            field=models.DateField(default=ocorrencia_erro.models.default_deadline, help_text='Data de previsão para término', verbose_name='Prazo'),
        ),
        migrations.AddField(
            model_name='record',
            name='device',
            field=models.CharField(default='N/A', help_text='Equipamento', max_length=100, verbose_name='Equipamento'),
        ),
        migrations.AddField(
            model_name='record',
            name='feedback_manager',
            field=models.TextField(blank=True, default='Não identificado', help_text='Feedback Manager', null=True, verbose_name='Feedback Manager'),
        ),
        migrations.AddField(
            model_name='record',
            name='feedback_technical',
            field=models.TextField(blank=True, default='Não identificado', help_text='Feedback Técnico', null=True, verbose_name='Feedback Técnico'),
        ),
        migrations.AddField(
            model_name='record',
            name='finished',
            field=models.DateField(blank=True, default=datetime.date.today, help_text='Data de previsão para término', null=True, verbose_name='Concluído em'),
        ),
        migrations.AddField(
            model_name='record',
            name='model',
            field=models.CharField(blank=True, default='N/A', help_text='Modelo', max_length=100, null=True, verbose_name='Modelo'),
        ),
        migrations.AddField(
            model_name='record',
            name='problem_detected',
            field=models.TextField(default='Não identificado', help_text='Problema detectado', verbose_name='Problema detectado'),
        ),
        migrations.AddField(
            model_name='record',
            name='responsible',
            field=models.CharField(default='Não identificado', help_text='Técnico responsável', max_length=100, verbose_name='Responsável'),
        ),
        migrations.AddField(
            model_name='record',
            name='serial',
            field=models.CharField(blank=True, default='N/A', help_text='Serial', max_length=20, null=True, verbose_name='Serial'),
        ),
        migrations.AddField(
            model_name='record',
            name='status',
            field=models.CharField(choices=[('done', 'Feito'), ('late', 'Atrasado'), ('progress', 'Em progresso'), ('requested', 'Requisitado')], default='requested', max_length=20),
        ),
        migrations.AddField(
            model_name='record',
            name='technical',
            field=models.CharField(default='Não identificado', help_text='Técnico que reportou', max_length=100, verbose_name='Técnico'),
        ),
        migrations.AddField(
            model_name='record',
            name='version',
            field=models.CharField(blank=True, default='N/A', help_text='Versão', max_length=100, null=True, verbose_name='Versão'),
        ),
        migrations.AddField(
            model_name='record',
            name='year',
            field=models.PositiveIntegerField(blank=True, default=0, help_text='Ano', null=True, verbose_name='Ano'),
        ),
        migrations.AlterField(
            model_name='record',
            name='data',
            field=models.DateField(default=datetime.date.today, help_text='Data de reporte', verbose_name='Data de reporte'),
        ),
    ]
