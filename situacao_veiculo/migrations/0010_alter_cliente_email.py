# Generated by Django 5.2.1 on 2025-05-27 15:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('situacao_veiculo', '0009_alter_cliente_cnpj_alter_cliente_email_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cliente',
            name='email',
            field=models.EmailField(blank=True, max_length=254, verbose_name='Email'),
        ),
    ]
