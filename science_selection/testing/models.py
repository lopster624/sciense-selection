from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from utils.constants import PSYCHOLOGICAL_TYPE_OF_TEST


class TypeOfTest(models.Model):
    """ Таблица с возможными типами тестов """

    name = models.CharField(max_length=128, verbose_name='Тип теста')

    class Meta:
        verbose_name = "Тип теста"
        verbose_name_plural = "Тип тестов"

    def __str__(self):
        return f'{self.name}'

    def is_psychological(self):
        return self.name == PSYCHOLOGICAL_TYPE_OF_TEST


class Test(models.Model):
    """ Таблица с тестами """

    name = models.CharField(max_length=128, verbose_name='Название теста')
    time_limit = models.IntegerField(verbose_name='Ограничение по времени (в мин.)', validators=[MinValueValidator(1)])
    description = models.CharField(max_length=256, verbose_name='Описание теста', blank=True)
    directions = models.ManyToManyField('application.Direction', verbose_name='Направления тестов', blank=True)
    creator = models.ForeignKey('account.Member', on_delete=models.CASCADE, verbose_name='Создатель теста')
    type = models.ForeignKey(TypeOfTest, on_delete=models.CASCADE, verbose_name='Тип теста')
    create_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['create_date']
        verbose_name = "Тест"
        verbose_name_plural = "Тесты"

    def __str__(self):
        return f'{self.name}-{self.creator}'


def validate_result(value):
    if value > 100 or value < 0:
        raise ValidationError(_(f'Результат должен находиться от 0 до 100'))


class TestResult(models.Model):
    """ Таблица с результатами тестов пользователей """

    test_statuses = [
        (1, 'Не начат'),
        (2, 'Начат'),
        (3, 'Закончен'),
    ]
    test = models.ForeignKey(Test, on_delete=models.CASCADE, verbose_name='Тесты', related_name='test_res')
    member = models.ForeignKey('account.Member', on_delete=models.CASCADE, verbose_name='Пользователь',
                               related_name='test_result')
    result = models.IntegerField(verbose_name='Результат тестирования', blank=True, validators=[validate_result])
    start_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата начала теста')
    end_date = models.DateTimeField(blank=True, verbose_name='Дата окончания теста')
    status = models.IntegerField(choices=test_statuses, default=1, verbose_name='Статус теста')

    class Meta:
        ordering = ['pk']
        verbose_name = "Результаты теста"
        verbose_name_plural = "Результаты тестов"

    def __str__(self):
        return f'{self.test} {self.status}'


class Question(models.Model):
    """ Таблица с вопросами для тестов """

    type_of_question = [
        (1, 'Один вариант ответа'),
        (2, 'Несколько вариантов ответа'),
        (3, 'Без правильных вариантов')
    ]
    test = models.ForeignKey(Test, on_delete=models.CASCADE, verbose_name='Номер теста')
    wording = models.CharField(max_length=256, verbose_name='Формулировка')
    question_type = models.IntegerField(choices=type_of_question, verbose_name='Количество вариантов')
    image = models.ImageField(upload_to='images/', blank=True, null=True, verbose_name='Изображение')

    class Meta:
        ordering = ['pk']
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"

    def __str__(self):
        return f'{self.test}-{self.wording}'


class Answer(models.Model):
    """ Таблица с вариантами ответов к вопросам """

    meaning = models.CharField(max_length=256, verbose_name='Ответ')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name='Вопрос',
                                 related_name='answer_options')
    is_correct = models.BooleanField(default=False, verbose_name='Правильный ответ')

    class Meta:
        verbose_name = "Ответ"
        verbose_name_plural = "Ответы"

    def __str__(self):
        return f'{self.meaning}'


class UserAnswer(models.Model):
    """ Таблица с вариантами ответов пользователей к вопросам """

    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name='Вопрос')
    member = models.ForeignKey('account.member', on_delete=models.CASCADE, verbose_name='Пользователь')
    answer_option = models.JSONField(verbose_name='Варианты ответа')

    class Meta:
        ordering = ['pk']
        verbose_name = "Ответ пользователя"
        verbose_name_plural = "Ответы пользователя"

    def __str__(self):
        return f'{self.question} {self.answer_option}'
