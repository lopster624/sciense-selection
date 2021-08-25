# Generated by Django 3.1.2 on 2021-08-25 08:47

import application.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('account', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdditionField',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, verbose_name='Название дополнительного поля')),
            ],
        ),
        migrations.CreateModel(
            name='Application',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('birth_day', models.DateField(verbose_name='День рождения')),
                ('birth_place', models.CharField(max_length=128, verbose_name='Место рождения')),
                ('nationality', models.CharField(max_length=128, verbose_name='Гражданство')),
                ('military_commissariat', models.CharField(max_length=128, verbose_name='Военный комиссариат')),
                ('group_of_health', models.CharField(max_length=32, verbose_name='Группа здоровья')),
                ('draft_year', models.IntegerField(validators=[application.models.validate_draft_year], verbose_name='Год призыва')),
                ('draft_season', models.IntegerField(choices=[(1, 'Осень'), (2, 'Весна')])),
                ('scientific_achievements', models.TextField(blank=True, null=True, verbose_name='Достижения')),
                ('scholarships', models.TextField(blank=True, null=True, verbose_name='')),
                ('ready_to_secret', models.BooleanField(default=False, verbose_name='Готовность к секретности')),
                ('candidate_exams', models.TextField(blank=True, null=True, verbose_name='Кандидатские экзамены')),
                ('sporting_achievements', models.TextField(blank=True, null=True, verbose_name='Спортивные достижения')),
                ('hobby', models.TextField(blank=True, null=True, verbose_name='Хобби')),
                ('other_information', models.TextField(blank=True, null=True, verbose_name='Дополнительная информация')),
                ('create_date', models.DateTimeField(auto_now_add=True)),
                ('update_date', models.DateTimeField(auto_now=True)),
                ('fullness', models.FloatField(default=0, verbose_name='Процент заполненности')),
                ('final_score', models.IntegerField(default=0, verbose_name='Итоговая оценка заявки')),
            ],
            options={
                'ordering': ['create_date'],
            },
        ),
        migrations.CreateModel(
            name='Direction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, verbose_name='Наименование направления')),
                ('description', models.TextField(verbose_name='Описание направления')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file_path', models.FilePathField(verbose_name='Путь к файлу')),
                ('file_name', models.CharField(max_length=128, verbose_name='Имя файла')),
                ('create_date', models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления файла')),
                ('is_template', models.BooleanField(default=False, verbose_name='Шаблон')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='account.member', verbose_name='Пользователь')),
            ],
        ),
        migrations.CreateModel(
            name='Education',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('education_type', models.CharField(choices=[('b', 'Бакалавриат'), ('m', 'Магистратура'), ('a', 'Аспирантура'), ('s', 'Специалитет')], max_length=1)),
                ('university', models.CharField(max_length=256, verbose_name='Университет')),
                ('specialization', models.CharField(max_length=256, verbose_name='Специальность')),
                ('avg_score', models.FloatField(validators=[application.models.validate_avg_score], verbose_name='Средний балл')),
                ('end_year', models.IntegerField(verbose_name='Год окончания')),
                ('is_ended', models.BooleanField(default=False, verbose_name='Окончено')),
                ('theme_of_diploma', models.CharField(max_length=128, verbose_name='Тема диплома')),
                ('application', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='application.application', verbose_name='Заявка')),
            ],
        ),
        migrations.CreateModel(
            name='Competence',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, verbose_name='Название компетенции')),
                ('is_estimated', models.BooleanField(default=False, verbose_name='Есть оценка')),
                ('directions', models.ManyToManyField(to='application.Direction')),
                ('parent_node', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='application.competence')),
            ],
        ),
        migrations.CreateModel(
            name='ApplicationCompetencies',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.IntegerField(choices=[(1, 'Базовый'), (2, 'Можешь писать программы'), (3, 'Бог')])),
                ('application', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='application.application')),
                ('competence', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='application.competence')),
            ],
        ),
        migrations.AddField(
            model_name='application',
            name='competencies',
            field=models.ManyToManyField(through='application.ApplicationCompetencies', to='application.Competence', verbose_name='Выбранные компетенции'),
        ),
        migrations.AddField(
            model_name='application',
            name='directions',
            field=models.ManyToManyField(to='application.Direction', verbose_name='Выбранные направления'),
        ),
        migrations.AddField(
            model_name='application',
            name='member',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='account.member', verbose_name='Пользователь'),
        ),
        migrations.CreateModel(
            name='AdditionFieldApp',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.TextField(verbose_name='Название дополнительного поля')),
                ('addition_field', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='application.additionfield', verbose_name='Название доп поля')),
                ('application', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='application.application', verbose_name='Заявка')),
                ('directions', models.ManyToManyField(to='application.Direction')),
            ],
        ),
        migrations.AddField(
            model_name='additionfield',
            name='directions',
            field=models.ManyToManyField(to='application.Direction'),
        ),
    ]
