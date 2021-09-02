# Generated by Django 3.2.7 on 2021-09-02 09:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0004_auto_20210902_1004'),
    ]

    operations = [
        migrations.AlterField(
            model_name='application',
            name='competencies',
            field=models.ManyToManyField(blank=True, through='application.ApplicationCompetencies', to='application.Competence', verbose_name='Выбранные компетенции'),
        ),
        migrations.AlterField(
            model_name='application',
            name='directions',
            field=models.ManyToManyField(blank=True, to='application.Direction', verbose_name='Выбранные направления'),
        ),
        migrations.AlterField(
            model_name='direction',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='images/', verbose_name='Изображения'),
        ),
    ]