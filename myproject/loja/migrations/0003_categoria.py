# Generated by Django 5.0.4 on 2024-09-23 17:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loja', '0002_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Categoria',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100)),
            ],
        ),
    ]
