# Generated by Django 3.2.9 on 2022-03-02 06:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0003_alter_member_father_name'),
        ('application', '0003_alter_education_avg_score'),
    ]

    operations = [
        migrations.AlterField(
            model_name='application',
            name='birth_place',
            field=models.CharField(help_text='Область, город', max_length=128, verbose_name='Место рождения'),
        ),
        migrations.AlterField(
            model_name='direction',
            name='description',
            field=models.TextField(blank=True, verbose_name='Описание направления'),
        ),
        migrations.CreateModel(
            name='AppsViewedByMaster',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('application', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='application.application', verbose_name='Заявка')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='account.member', verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Просмотренная заявка пользователем',
                'verbose_name_plural': 'Просмотренные заявки пользователями',
            },
        ),
    ]