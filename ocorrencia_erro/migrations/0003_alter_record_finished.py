# Generated by Django 5.2.1 on 2025-06-04 14:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ocorrencia_erro', '0002_record_area_record_brand_record_country_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='record',
            name='finished',
            field=models.DateField(blank=True, help_text='Data de previsão para término', null=True, verbose_name='Concluído em'),
        ),
    ]
