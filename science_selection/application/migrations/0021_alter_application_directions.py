# Generated by Django 3.2.6 on 2021-09-28 07:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0020_auto_20210917_1643'),
    ]

    operations = [
        migrations.AlterField(
            model_name='application',
            name='directions',
            field=models.ManyToManyField(blank=True, related_name='application', to='application.Direction', verbose_name='Выбранные направления'),
        ),
    ]