# Generated by Django 3.2.9 on 2022-06-16 06:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0005_alter_education_theme_of_diploma'),
    ]

    operations = [
        migrations.AddField(
            model_name='application',
            name='suitable',
            field=models.BooleanField(default=False, verbose_name='Подходит или нет по его данным: средний балл и т.д.'),
        ),
    ]
