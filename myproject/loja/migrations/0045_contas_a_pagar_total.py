# Generated by Django 5.0.4 on 2025-03-06 17:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loja', '0044_alter_custos_extras_data_pg_alter_custos_extras_obs_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='contas_a_pagar',
            name='total',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
