# Generated by Django 3.2.6 on 2021-09-17 09:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0014_merge_20210916_1033'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='applicationnote',
            options={'verbose_name': 'Заметка об анкете', 'verbose_name_plural': 'Заметки об анкетах'},
        ),
        migrations.AddField(
            model_name='application',
            name='a1',
            field=models.FloatField(blank=True, default=0.0, verbose_name='Оценка кандидата по критерию "Склонность к научной деятельности"'),
        ),
        migrations.AddField(
            model_name='application',
            name='a2',
            field=models.FloatField(blank=True, default=0.0, verbose_name='Оценка кандидата по критерию "Средний балл диплома о высшем образовании"'),
        ),
        migrations.AddField(
            model_name='application',
            name='a3',
            field=models.FloatField(blank=True, default=0.0, verbose_name='Оценка кандидата по критерию "Соответствие направления подготовки высшего образования кандидата профилю научных исследований,выполняемых соответствующей научной ротой"'),
        ),
        migrations.AddField(
            model_name='application',
            name='a4',
            field=models.FloatField(blank=True, default=0.0, verbose_name='Оценка кандидата по критерию "Результативность образовательной деятельности"'),
        ),
        migrations.AddField(
            model_name='application',
            name='a5',
            field=models.FloatField(blank=True, default=0.0, verbose_name='Оценка кандидата по критерию "Подготовка по программе аспирантуры и наличие ученой степени"'),
        ),
        migrations.AddField(
            model_name='application',
            name='a6',
            field=models.FloatField(blank=True, default=0.0, verbose_name='Оценка кандидата по критерию "Опыт работы по профилю научных исследований, выполняемых соответствующей научной ротой"'),
        ),
        migrations.AddField(
            model_name='application',
            name='a7',
            field=models.FloatField(blank=True, default=0.0, verbose_name='Оценка кандидата по критерию "Мотивация к военной службе"'),
        ),
        migrations.AddField(
            model_name='application',
            name='city_olympics',
            field=models.BooleanField(default=False, verbose_name='Наличие призовых мест на олимпиадах на уровне города'),
        ),
        migrations.AddField(
            model_name='application',
            name='commercial_experience',
            field=models.BooleanField(default=False, verbose_name='Наличие опыта работы по специальности в коммерческих предприятиях (не менее 1 года)'),
        ),
        migrations.AddField(
            model_name='application',
            name='compliance_additional_direction',
            field=models.BooleanField(default=False, verbose_name='Соответствие дополнительному направлению высшего образования'),
        ),
        migrations.AddField(
            model_name='application',
            name='compliance_prior_direction',
            field=models.BooleanField(default=False, verbose_name='Соответствие приоритетному направлению высшего образования'),
        ),
        migrations.AddField(
            model_name='application',
            name='country_olympics',
            field=models.BooleanField(default=False, verbose_name='Наличие призовых мест на олимпиадах всероссийского уровня'),
        ),
        migrations.AddField(
            model_name='application',
            name='evm_register',
            field=models.BooleanField(default=False, verbose_name='Наличие свидетельств о регистрации баз данных и программ для ЭВМ'),
        ),
        migrations.AddField(
            model_name='application',
            name='government_scholarship',
            field=models.BooleanField(default=False, verbose_name='Стипендиат государственных стипендий Правительства Российской Федерации'),
        ),
        migrations.AddField(
            model_name='application',
            name='innovation_proposals',
            field=models.BooleanField(default=False, verbose_name='Наличие свидетельств нарационализаторские предложения'),
        ),
        migrations.AddField(
            model_name='application',
            name='international_articles',
            field=models.BooleanField(default=False, verbose_name='Наличие опубликованных научных статей в международных изданиях'),
        ),
        migrations.AddField(
            model_name='application',
            name='international_olympics',
            field=models.BooleanField(default=False, verbose_name='Наличие призовых мест на международных олимпиадах'),
        ),
        migrations.AddField(
            model_name='application',
            name='military_grants',
            field=models.BooleanField(default=False, verbose_name='Обладательгрантов по научным работам, имеющим прикладное значение дляМинобороны России, которые подтверждены органами военного управления'),
        ),
        migrations.AddField(
            model_name='application',
            name='military_sport_achievements',
            field=models.BooleanField(default=False, verbose_name='Наличие спортивных достижений по военно-прикладным видам спорта, в том числе выполнение нормативов ГТО'),
        ),
        migrations.AddField(
            model_name='application',
            name='opk_experience',
            field=models.BooleanField(default=False, verbose_name='Наличие опыта работы по специальности на предприятиях ОПК (не менее 1 года)'),
        ),
        migrations.AddField(
            model_name='application',
            name='patents',
            field=models.BooleanField(default=False, verbose_name='Наличие патентов на изобретения и полезные модели'),
        ),
        migrations.AddField(
            model_name='application',
            name='president_scholarship',
            field=models.BooleanField(default=False, verbose_name='Стипендиат государственных стипендий Президента Российской Федерации'),
        ),
        migrations.AddField(
            model_name='application',
            name='region_olympics',
            field=models.BooleanField(default=False, verbose_name='Наличие призовых мест на олимпиадах областного уровня'),
        ),
        migrations.AddField(
            model_name='application',
            name='rinc_articles',
            field=models.BooleanField(default=False, verbose_name='Наличие опубликованных научных статей в изданиях РИНЦ'),
        ),
        migrations.AddField(
            model_name='application',
            name='science_experience',
            field=models.BooleanField(default=False, verbose_name='Наличие опыта работы по специальности в научных организациях (подразделениях) на должностях научных сотрудников (не менее 1 года)'),
        ),
        migrations.AddField(
            model_name='application',
            name='sport_achievements',
            field=models.BooleanField(default=False, verbose_name='Наличие спортивных достижений по иным видам спорта'),
        ),
        migrations.AddField(
            model_name='application',
            name='vac_articles',
            field=models.BooleanField(default=False, verbose_name='Наличие опубликованных научных статей в научных изданиях, рекомендуемых ВАК'),
        ),
        migrations.AlterField(
            model_name='applicationnote',
            name='application',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='application.application', verbose_name='Анкета'),
        ),
    ]
