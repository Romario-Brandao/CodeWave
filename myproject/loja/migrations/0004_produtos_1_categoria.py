# Generated by Django 5.0.4 on 2024-09-23 17:03

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loja', '0003_categoria'),
    ]

    operations = [
        migrations.AddField(
            model_name='produtos_1',
            name='categoria',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='loja.categoria'),
        ),
    ]
