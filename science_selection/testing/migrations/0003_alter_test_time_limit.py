# Generated by Django 3.2.7 on 2021-11-30 06:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testing', '0002_auto_20211126_1009'),
    ]

    operations = [
        migrations.AlterField(
            model_name='test',
            name='time_limit',
            field=models.IntegerField(verbose_name='Ограничение по времени (в мин.)'),
        ),
    ]
