# Generated by Django 5.0.4 on 2025-03-06 01:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loja', '0041_custos_extras_acrescimo_custos_extras_desconto_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='custos_extras',
            name='obs',
            field=models.CharField(default='', max_length=50),
        ),
    ]
