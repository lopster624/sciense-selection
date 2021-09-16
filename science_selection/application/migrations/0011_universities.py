# Generated by Django 3.2.7 on 2021-09-16 06:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0010_auto_20210914_1635'),
    ]

    operations = [
        migrations.CreateModel(
            name='Universities',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256, verbose_name='Название университета')),
                ('rating_place', models.IntegerField(blank=True, verbose_name='Рейтинговое место')),
            ],
        ),
    ]
