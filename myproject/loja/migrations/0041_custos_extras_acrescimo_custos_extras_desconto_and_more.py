# Generated by Django 5.0.4 on 2025-03-06 01:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loja', '0040_rename_n_caixa_custos_extras_n_servico'),
    ]

    operations = [
        migrations.AddField(
            model_name='custos_extras',
            name='acrescimo',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='custos_extras',
            name='desconto',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='custos_extras',
            name='total',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
