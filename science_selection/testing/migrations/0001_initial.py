# Generated by Django 3.2.7 on 2021-10-21 06:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('account', '0012_alter_member_phone'),
        ('application', '0028_militarycommissariat_specialization'),
    ]

    operations = [
        migrations.CreateModel(
            name='Testing',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, verbose_name='Название теста')),
                ('time_limit', models.IntegerField(verbose_name='Ограничение по времени (в мин.)')),
                ('description', models.CharField(max_length=256, verbose_name='Описание теста')),
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
        ),
        migrations.CreateModel(
            name='TestResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('result', models.IntegerField(blank=True, verbose_name='Результат тестирования')),
                ('start_date', models.DateTimeField(auto_now_add=True, verbose_name='Дата начала теста')),
                ('end_date', models.DateTimeField(blank=True, verbose_name='Дата окончания теста')),
                ('status', models.IntegerField(choices=[(1, 'Не начат'), (2, 'Начат'), (3, 'Закончен')], default=1, verbose_name='Статус теста')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='account.member', verbose_name='Пользователь')),
                ('test', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='testing', to='testing.testing', verbose_name='Тесты')),
            ],
            options={
                'verbose_name': 'Результаты теста',
                'verbose_name_plural': 'Результаты тестов',
                'ordering': ['pk'],
            },
        ),
        migrations.AddField(
            model_name='testing',
            name='type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='testing.typeoftest', verbose_name='Тип теста'),
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('wording', models.CharField(max_length=256, verbose_name='Формулировка вопроса')),
                ('answer_options', models.JSONField(verbose_name='Варианты ответов')),
                ('correct_answers', models.JSONField(verbose_name='Правильные ответы')),
                ('question_type', models.IntegerField(choices=[(1, 'Один вариант ответа'), (2, 'Несколько вариантов ответа')], verbose_name='Тип вопроса')),
                ('image', models.ImageField(blank=True, null=True, upload_to='images/', verbose_name='Картинка')),
                ('test', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='testing.testing', verbose_name='Номер теста')),
            ],
            options={
                'verbose_name': 'Вопрос',
                'verbose_name_plural': 'Вопросы',
                'ordering': ['pk'],
            },
        ),
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer_option', models.JSONField(verbose_name='Вариант ответа')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='account.member', verbose_name='Пользователь')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='testing.question', verbose_name='Вопрос')),
            ],
            options={
                'verbose_name': 'Ответ',
                'verbose_name_plural': 'Ответы',
                'ordering': ['pk'],
            },
        ),
    ]