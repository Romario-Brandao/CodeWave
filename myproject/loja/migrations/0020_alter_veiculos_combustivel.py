# Generated by Django 5.0.4 on 2025-01-13 16:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loja', '0019_fornecedor_endereco'),
    ]

    operations = [
        migrations.AlterField(
            model_name='veiculos',
            name='combustivel',
            field=models.CharField(default='NÃO CADASTRADO', max_length=20),
            preserve_default=False,
        ),
    ]
