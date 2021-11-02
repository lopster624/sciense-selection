# Generated by Django 3.2.7 on 2021-10-26 06:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('testing', '0002_auto_20211025_1516'),
    ]

    operations = [
        migrations.AlterField(
            model_name='answer',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answer_options', to='testing.question', verbose_name='Вопрос'),
        ),
        migrations.AlterField(
            model_name='question',
            name='correct_answers',
            field=models.JSONField(blank=True, verbose_name='Правильные ответы'),
        ),
        migrations.AlterField(
            model_name='testresult',
            name='test',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='test_res', to='testing.testing', verbose_name='Тесты'),
        ),
    ]