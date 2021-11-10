from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _


class TypeOfTest(models.Model):
    name = models.CharField(max_length=128, verbose_name='Тип теста')

    class Meta:
        verbose_name = "Тип теста"
        verbose_name_plural = "Тип тестов"

    def __str__(self):
        return f'{self.name}'

    def is_psychological(self):
        return True if self.name == 'Психологический' else False


class Testing(models.Model):
    name = models.CharField(max_length=128, verbose_name='Название теста')
    time_limit = models.IntegerField(verbose_name='Ограничение по времени (в мин.)', validators=[MinValueValidator(1)])
    description = models.CharField(max_length=256, verbose_name='Описание теста', blank=True)
    directions = models.ManyToManyField('application.Direction', verbose_name='Направления тестов', blank=True, )
    creator = models.ForeignKey('account.Member', on_delete=models.CASCADE, verbose_name='Создатель теста')
    type = models.ForeignKey(TypeOfTest, on_delete=models.CASCADE, verbose_name='Тип теста')
    create_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['create_date']
        verbose_name = "Тест"
        verbose_name_plural = "Тесты"

    def __str__(self):
        return f'{self.name} {self.creator}'


def validate_result(value):
    if value > 100 or value < 0:
        raise ValidationError(_(f'Результат должен находиться от 0 до 100'))


class TestResult(models.Model):
    test_statuses = [
        (1, 'Не начат'),
        (2, 'Начат'),
        (3, 'Закончен'),
    ]
    test = models.ForeignKey(Testing, on_delete=models.CASCADE, verbose_name='Тесты', related_name='test_res')
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
    type_of_question = [
        (1, 'Один вариант ответа'),
        (2, 'Несколько вариантов ответа')
    ]
    test = models.ForeignKey(Testing, on_delete=models.CASCADE, verbose_name='Номер теста')
    wording = models.CharField(max_length=256, verbose_name='Формулировка вопроса')
    correct_answers = models.JSONField(verbose_name='Правильные ответы', blank=True)
    question_type = models.IntegerField(choices=type_of_question, verbose_name='Тип вопроса')
    image = models.ImageField(upload_to='images/', blank=True, null=True, verbose_name='Картинка')

    class Meta:
        ordering = ['pk']
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"

    def __str__(self):
        return f'{self.test} {self.wording}'


class Answer(models.Model):
    meaning = models.CharField(max_length=256, verbose_name='Ответ к вопросу')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name='Вопрос',
                                 related_name='answer_options')

    class Meta:
        verbose_name = "Ответ"
        verbose_name_plural = "Ответы"

    def __str__(self):
        return f'{self.meaning}'


class UserAnswer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name='Вопрос')
    member = models.ForeignKey('account.member', on_delete=models.CASCADE, verbose_name='Пользователь')
    answer_option = models.JSONField(verbose_name='Варианты ответа')

    class Meta:
        ordering = ['pk']
        verbose_name = "Ответ пользователя"
        verbose_name_plural = "Ответы пользователя"

    def __str__(self):
        return f'{self.question} {self.answer_option}'
