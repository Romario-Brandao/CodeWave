# Generated by Django 5.0.4 on 2025-03-07 02:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loja', '0045_contas_a_pagar_total'),
    ]

    operations = [
        migrations.AddField(
            model_name='contas_receber',
            name='total',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
