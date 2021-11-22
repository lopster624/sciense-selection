# Generated by Django 3.2.7 on 2021-11-18 09:22

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import testing.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('application', '0032_merge_20211117_1243'),
        ('account', '0012_alter_member_phone'),
    ]

    operations = [
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('meaning', models.CharField(max_length=256, verbose_name='Ответ')),
            ],
            options={
                'verbose_name': 'Ответ',
                'verbose_name_plural': 'Ответы',
            },
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('wording', models.CharField(max_length=256, verbose_name='Формулировка')),
                ('question_type', models.IntegerField(choices=[(1, 'Один вариант ответа'), (2, 'Несколько вариантов ответа'), (3, 'Без правильных вариантов')], verbose_name='Количество вариантов')),
                ('image', models.ImageField(blank=True, null=True, upload_to='images/', verbose_name='Изображение')),
            ],
            options={
                'verbose_name': 'Вопрос',
                'verbose_name_plural': 'Вопросы',
                'ordering': ['pk'],
            },
        ),
        migrations.CreateModel(
            name='Test',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, verbose_name='Название теста')),
                ('time_limit', models.IntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name='Ограничение по времени (в мин.)')),
                ('description', models.CharField(blank=True, max_length=256, verbose_name='Описание теста')),
                ('create_date', models.DateTimeField(auto_now_add=True)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='account.member', verbose_name='Создатель теста')),
                ('directions', models.ManyToManyField(blank=True, to='application.Direction', verbose_name='Направления тестов')),
            ],
            options={
                'verbose_name': 'Тест',
                'verbose_name_plural': 'Тесты',
                'ordering': ['create_date'],
            },
        ),
        migrations.CreateModel(
            name='TypeOfTest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, verbose_name='Тип теста')),
            ],
            options={
                'verbose_name': 'Тип теста',
                'verbose_name_plural': 'Тип тестов',
            },
        ),
        migrations.CreateModel(
            name='UserAnswer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer_option', models.JSONField(verbose_name='Варианты ответа')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='account.member', verbose_name='Пользователь')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='testing.question', verbose_name='Вопрос')),
            ],
            options={
                'verbose_name': 'Ответ пользователя',
                'verbose_name_plural': 'Ответы пользователя',
                'ordering': ['pk'],
            },
        ),
        migrations.CreateModel(
            name='TestResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('result', models.IntegerField(blank=True, validators=[testing.models.validate_result], verbose_name='Результат тестирования')),
                ('start_date', models.DateTimeField(auto_now_add=True, verbose_name='Дата начала теста')),
                ('end_date', models.DateTimeField(blank=True, verbose_name='Дата окончания теста')),
                ('status', models.IntegerField(choices=[(1, 'Не начат'), (2, 'Начат'), (3, 'Закончен')], default=1, verbose_name='Статус теста')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='test_result', to='account.member', verbose_name='Пользователь')),
                ('test', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='test_res', to='testing.test', verbose_name='Тесты')),
            ],
            options={
                'verbose_name': 'Результаты теста',
                'verbose_name_plural': 'Результаты тестов',
                'ordering': ['pk'],
            },
        ),
        migrations.AddField(
            model_name='test',
            name='type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='testing.typeoftest', verbose_name='Тип теста'),
        ),
        migrations.AddField(
            model_name='question',
            name='test',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='testing.test', verbose_name='Номер теста'),
        ),
        migrations.CreateModel(
            name='CorrectAnswer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='testing.answer', verbose_name='Ответ')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='correct_answer', to='testing.question', verbose_name='Вопрос')),
            ],
            options={
                'verbose_name': 'Правильный ответ',
                'verbose_name_plural': 'Правильные ответы',
            },
        ),
        migrations.AddField(
            model_name='answer',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answer_options', to='testing.question', verbose_name='Вопрос'),
        ),
    ]
