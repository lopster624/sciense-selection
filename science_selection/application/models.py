import datetime

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from utils import constants as const
from account.models import Member


def validate_draft_year(value: int):
    if value < datetime.date.today().year:
        raise ValidationError(_(f'Год призыва {value} раньше текущего'))


class Application(models.Model):
    season = [
        (1, 'Осень'),
        (2, 'Весна')
    ]
    member = models.OneToOneField(Member, on_delete=models.CASCADE, verbose_name='Пользователь')
    competencies = models.ManyToManyField('Competence', verbose_name='Выбранные компетенции',
                                          through='ApplicationCompetencies')
    directions = models.ManyToManyField('Direction', verbose_name='Выбранные направления')
    birth_day = models.DateField(verbose_name='Дата рождения')
    birth_place = models.CharField(max_length=128, verbose_name='Место рождения')
    nationality = models.CharField(max_length=128, verbose_name='Гражданство')
    military_commissariat = models.CharField(max_length=128, verbose_name='Военный комиссариат')
    group_of_health = models.CharField(max_length=32, verbose_name='Группа здоровья')
    draft_year = models.IntegerField(verbose_name='Год призыва', validators=[validate_draft_year])
    draft_season = models.IntegerField(choices=season, verbose_name='Сезон призыва')
    scientific_achievements = models.TextField(blank=True, verbose_name='Достижения', help_text='Статьи ВАК, РИМС ...')
    scholarships = models.TextField(blank=True, verbose_name='Стипендии')
    ready_to_secret = models.BooleanField(default=False, verbose_name='Готовность к секретности')
    candidate_exams = models.TextField(blank=True, verbose_name='Кандидатские экзамены')
    sporting_achievements = models.TextField(blank=True, verbose_name='Спортивные достижения', help_text='Разряды ...')
    hobby = models.TextField(blank=True, verbose_name='Хобби')
    other_information = models.TextField(blank=True, verbose_name='Дополнительная информация')
    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)
    fullness = models.FloatField(default=0, verbose_name='Процент заполненности')
    final_score = models.IntegerField(default=0, verbose_name='Итоговая оценка заявки')

    class Meta:
        ordering = ['create_date']
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"

    def calculate_fullness(self) -> int:
        """
        Подсчет заполненности анкеты
        :return: значение заполненности в %
        """
        return 1

    def calculate_final_score(self) -> float:
        """
        Подсчет рейтингового балла заявки оператора по формуле
        :return: рассчитание значение
        """
        return 1

    def save(self, *args, **kwargs):
        self.fullness = self.calculate_fullness()
        self.final_score = self.calculate_final_score()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.member.user.first_name} {self.member.user.last_name}'


def validate_avg_score(value: float):
    if value < const.MINIMUM_SCORE or value > const.MAX_SCORE:
        raise ValidationError(_(f'Некорректный средний балл: {value}'))


class Education(models.Model):
    education_program = [
        ('b', 'Бакалавриат'),
        ('m', 'Магистратура'),
        ('a', 'Аспирантура'),
        ('s', 'Специалитет'),
    ]
    application = models.ForeignKey(Application, on_delete=models.CASCADE, verbose_name='Заявка')
    education_type = models.CharField(choices=education_program, max_length=1, verbose_name='Программа')
    university = models.CharField(max_length=256, verbose_name='Университет')
    specialization = models.CharField(max_length=256, verbose_name='Специальность')
    avg_score = models.FloatField(verbose_name='Средний балл', validators=[validate_avg_score])
    end_year = models.IntegerField(verbose_name='Год окончания')
    is_ended = models.BooleanField(default=False, verbose_name='Окончено')
    theme_of_diploma = models.CharField(max_length=128, verbose_name='Тема диплома')

    def __str__(self):
        return f'{self.application.member.user.first_name} {self.application.member.user.first_name}: {self.get_education_type_display()}'

    class Meta:
        verbose_name = "Образование"
        verbose_name_plural = "Образование"


class Direction(models.Model):
    name = models.CharField(max_length=128, verbose_name='Наименование направления')
    description = models.TextField(verbose_name='Описание направления')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = "Направление"
        verbose_name_plural = "Направления"


def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<timestamp>_<filename>
    return f'user_{instance.member.user.username}/{{int(datetime.datetime.timestamp(datetime.datetime.now()))}}_{filename}'


class File(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, verbose_name='Пользователь')
    file_path = models.FileField(upload_to=user_directory_path, verbose_name='Путь к файлу')
    file_name = models.CharField(max_length=128, verbose_name='Имя файла')
    create_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления файла')
    is_template = models.BooleanField(default=False, verbose_name='Шаблон')

    def __str__(self):
        return self.file_name

    class Meta:
        verbose_name = "Вложение"
        verbose_name_plural = "Вложения"


class AdditionField(models.Model):
    directions = models.ManyToManyField(Direction)
    name = models.CharField(max_length=128, verbose_name='Название дополнительного поля')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Кастомное поле"
        verbose_name_plural = "Кастомные поля"
        ordering = ['name']


class AdditionFieldApp(models.Model):
    directions = models.ManyToManyField(Direction)
    addition_field = models.ForeignKey(AdditionField, on_delete=models.CASCADE, verbose_name='Название доп поля')
    application = models.ForeignKey(Application, on_delete=models.CASCADE, verbose_name='Заявка')
    value = models.TextField(verbose_name='Название дополнительного поля')

    class Meta:
        verbose_name = "Значение кастомного поля"
        verbose_name_plural = "Значения кастомных полей"


class Competence(models.Model):
    parent_node = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    directions = models.ManyToManyField(Direction)
    name = models.CharField(max_length=128, verbose_name='Название компетенции')
    is_estimated = models.BooleanField(default=False, verbose_name='Есть оценка')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Компетенция"
        verbose_name_plural = "Компетенции"
        ordering = ['name']


class ApplicationCompetencies(models.Model):
    competence_level = [
        (1, 'Базовый'),
        (2, 'Можешь писать программы'),
        (3, 'Бог')
    ]
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    competence = models.ForeignKey(Competence, on_delete=models.CASCADE)
    level = models.IntegerField(choices=competence_level)

    class Meta:
        verbose_name = "Выбранная компетенция"
        verbose_name_plural = "Выбранные компетенции"

    def __str__(self):
        return f'{self.application.member.user.first_name}: {self.competence.name}'
