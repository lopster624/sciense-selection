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
        (1, 'Весна'),
        (2, 'Осень')
    ]
    member = models.OneToOneField(Member, on_delete=models.CASCADE, verbose_name='Пользователь',
                                  related_name='application')
    competencies = models.ManyToManyField('Competence', verbose_name='Выбранные компетенции',
                                          through='ApplicationCompetencies', blank=True)
    directions = models.ManyToManyField('Direction', verbose_name='Выбранные направления', blank=True)
    birth_day = models.DateField(verbose_name='Дата рождения')
    birth_place = models.CharField(max_length=128, verbose_name='Место рождения')
    nationality = models.CharField(max_length=128, verbose_name='Гражданство')
    military_commissariat = models.CharField(max_length=128, verbose_name='Военный комиссариат')
    group_of_health = models.CharField(max_length=32, verbose_name='Группа здоровья')
    draft_year = models.IntegerField(verbose_name='Год призыва', validators=[validate_draft_year])
    draft_season = models.IntegerField(choices=season, verbose_name='Сезон призыва')
    scientific_achievements = models.TextField(blank=True, verbose_name='Научные достижения', help_text='Участие в конкурсах, олимпиадах, издательской деятельности, '
                                                                                                        'научно-практические конференции, наличие патентов на изобретения, '
                                                                                                        'свидетельств о регистрации программ, свидетельств о рационализаторских предложениях и т.п.')
    scholarships = models.TextField(blank=True, verbose_name='Стипендии', help_text='Наличие грантов, именных премий, именных стипендий и т.п.')
    ready_to_secret = models.BooleanField(default=False, verbose_name='Готовность к секретности',
                                          help_text='Готовность гражданина к оформлению допуска к сведениям, содержащим государственную тайну, по 3 форме')
    candidate_exams = models.TextField(blank=True, verbose_name='Кандидатские экзамены',
                                       help_text='Наличие оформленного соискательства ученой степени и сданных экзаменов кандидатского минимума')
    sporting_achievements = models.TextField(blank=True, verbose_name='Спортивные достижения', help_text='Наличие спортивных достижений и разрядов')
    hobby = models.TextField(blank=True, verbose_name='Хобби', help_text='Увлечения и хобби')
    other_information = models.TextField(blank=True, verbose_name='Дополнительная информация')
    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)
    fullness = models.IntegerField(default=0, verbose_name='Процент заполненности')
    final_score = models.IntegerField(default=0, verbose_name='Итоговая оценка заявки')

    class Meta:
        ordering = ['create_date']
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"

    def get_filed_blocks(self):
        return {
            'Основные данные': True,
            'Образование': True if self.education.all() else False,
            'Направления': True if self.directions.all() else False,
            'Компетенции': True if self.competencies.all() else False,
            'Загруженные файлы': True if File.objects.filter(member=self.member) else False,
        }

    def calculate_fullness(self) -> int:
        """
        Подсчет заполненности анкеты
        :return: значение заполненности в %
        """
        filed_blocks = self.get_filed_blocks()
        fullness = [v for k, v in filed_blocks.items() if v]
        return int(len(fullness) / len(filed_blocks) * 100)

    def calculate_final_score(self) -> float:
        """
        Подсчет рейтингового балла заявки оператора по формуле
        :return: рассчитание значение
        """
        return 1

    def get_draft_time(self):
        return f'{self.season[self.draft_season - 1][1]} {self.draft_year}'

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
    application = models.ForeignKey(Application, on_delete=models.CASCADE, verbose_name='Заявка',
                                    related_name='education')
    education_type = models.CharField(choices=education_program, max_length=1, verbose_name='Программа')
    university = models.CharField(max_length=256, verbose_name='Университет')
    specialization = models.CharField(max_length=256, verbose_name='Специальность')
    avg_score = models.FloatField(verbose_name='Средний балл', validators=[validate_avg_score], blank=True)
    end_year = models.IntegerField(verbose_name='Год окончания')
    is_ended = models.BooleanField(default=False, verbose_name='Окончено')
    name_of_education_doc = models.CharField(max_length=256, verbose_name='Наименование документа об образовании', blank=True)
    theme_of_diploma = models.CharField(max_length=128, verbose_name='Тема диплома')

    def __str__(self):
        return f'{self.application.member.user.first_name} {self.application.member.user.first_name}: {self.get_education_type_display()}'

    def get_education_type_display(self):
        return next(name for ed_type, name in self.education_program if ed_type == self.education_type)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.application.save()

    class Meta:
        verbose_name = "Образование"
        verbose_name_plural = "Образование"


class Direction(models.Model):
    name = models.CharField(max_length=128, verbose_name='Наименование направления')
    description = models.TextField(verbose_name='Описание направления')
    image = models.ImageField(upload_to='images/', blank=True, null=True, verbose_name='Изображения')

    @property
    def image_url(self):
        if self.image and hasattr(self.image, 'url'):
            return self.image.url

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = "Направление"
        verbose_name_plural = "Направления"


class File(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, verbose_name='Пользователь')
    file_path = models.FileField(upload_to='files/%Y/%m/%d', verbose_name='Путь к файлу')
    file_name = models.CharField(max_length=128, verbose_name='Имя файла', blank=True)
    create_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления файла')
    is_template = models.BooleanField(default=False, verbose_name='Шаблон')

    def __str__(self):
        return self.file_name

    class Meta:
        verbose_name = "Вложение"
        verbose_name_plural = "Вложения"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.member.application.save()


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
    parent_node = models.ForeignKey('self', on_delete=models.CASCADE, verbose_name='Компетенция-родитель', null=True,
                                    blank=True, related_name='child')
    directions = models.ManyToManyField(Direction, verbose_name='Название направления', blank=True)
    name = models.CharField(max_length=128, verbose_name='Название компетенции')
    is_estimated = models.BooleanField(default=False, verbose_name='Есть оценка')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Компетенция"
        verbose_name_plural = "Компетенции"
        ordering = ['name']


class ApplicationCompetencies(models.Model):
    competence_levels = [
        (0, ''),
        (1, 'Базовый'),
        (2, 'Можешь писать программы'),
        (3, 'Бог')
    ]
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    competence = models.ForeignKey(Competence, on_delete=models.CASCADE)
    level = models.IntegerField(choices=competence_levels)

    class Meta:
        verbose_name = "Выбранная компетенция"
        verbose_name_plural = "Выбранные компетенции"

    def __str__(self):
        return f'{self.application.member.user.first_name}: {self.competence.name}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.application.save()


class Universities(models.Model):
    name = models.CharField(max_length=256, verbose_name='Название университета', )
    rating_place = models.IntegerField(verbose_name='Рейтинговое место', null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Университет'
        verbose_name_plural = 'Университеты'
