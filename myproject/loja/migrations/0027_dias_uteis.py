# Generated by Django 5.0.4 on 2025-01-30 00:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loja', '0026_profissional_ativo_alter_profissional_email_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Dias_uteis',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mes_ano', models.CharField(max_length=7, unique=True)),
                ('Dias_uteis', models.IntegerField(default=0, max_length=2)),
            ],
        ),
    ]
