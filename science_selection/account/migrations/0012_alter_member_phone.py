# Generated by Django 3.2.7 on 2021-10-13 08:32

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0011_alter_affiliation_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='member',
            name='phone',
            field=models.CharField(max_length=17, validators=[django.core.validators.RegexValidator(message='Введите корректный номер телефона формата: +79998887766', regex='^\\+?1?\\d{9,15}$')], verbose_name='Телефон'),
        ),
    ]
