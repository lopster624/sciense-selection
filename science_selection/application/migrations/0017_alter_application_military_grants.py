# Generated by Django 3.2.6 on 2021-09-17 12:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0016_auto_20210917_1513'),
    ]

    operations = [
        migrations.AlterField(
            model_name='application',
            name='military_grants',
            field=models.BooleanField(default=False, verbose_name='Обладательгрантов по научным работам, имеющим прикладное значение для Минобороны России, которые подтверждены органами военного управления'),
        ),
    ]