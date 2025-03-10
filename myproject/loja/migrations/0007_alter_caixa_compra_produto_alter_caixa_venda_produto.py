# Generated by Django 5.0.4 on 2024-09-24 19:45

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loja', '0006_unidade_medida_produtos_1_unidade_medida'),
    ]

    operations = [
        migrations.AlterField(
            model_name='caixa_compra',
            name='produto',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='loja.produtos_1'),
        ),
        migrations.AlterField(
            model_name='caixa_venda',
            name='produto',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='loja.produtos_1'),
        ),
    ]
