from django.contrib import admin

from . import models


@admin.register(models.Test)
class TestingAdmin(admin.ModelAdmin):
    list_display = ('name', 'time_limit', 'creator', 'get_directions')
    list_filter = ('name', 'creator')

    def get_directions(self, obj):
        return '; '.join([d.__str__() for d in obj.directions.all()])

    get_directions.short_descriptions = 'Направления'


@admin.register(models.TypeOfTest)
class TypeOfTestAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(models.TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ('test', 'member', 'result', 'status')
    list_filter = ('member', 'test', 'result')


@admin.register(models.UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'member', 'answer_option')


class AnswerInlineAdmin(admin.TabularInline):
    model = models.Answer
    fields = ['id', 'meaning']


@admin.register(models.Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('test', 'wording')
    list_filter = ('wording', 'test')
    inlines = [AnswerInlineAdmin]


@admin.register(models.Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('pk', 'meaning',)
