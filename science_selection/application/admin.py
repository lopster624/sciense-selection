from django.contrib import admin
from django.conf.urls import url
from django.shortcuts import render

from engine.middleware import logger

from . import models
from .utils import Questionnaires


class CompetenciesInlineAdmin(admin.TabularInline):
    model = models.Application.competencies.through


@admin.register(models.Application)
class ApplicationAdmin(admin.ModelAdmin):
    change_list_template = "admin/application_change_list.html"

    inlines = [CompetenciesInlineAdmin]
    list_display = ('member', 'draft_year', 'draft_season', 'final_score')
    list_filter = ('draft_year', 'draft_season', 'final_score')

    def get_urls(self):
        urls = super(ApplicationAdmin, self).get_urls()
        custom_urls = [
            url('^import/$', self.process_import, name='process_import')]
        return custom_urls + urls

    def process_import(self, request):
        # https: // habr.com / ru / company / cloud4y / blog / 650357 /
        # TODO; было бы хорошо создавать таски на выполнение этих задач, но вряд ли это будем делать)))
        new_files = request.FILES.getlist('downloaded_files')
        overall_result = []
        for file in new_files:
            questionnaires = Questionnaires(file=file)
            result = questionnaires.add_applications_to_db()
            overall_result.append(result)
            logger.info(result)
        return render(request, 'import.html', context={'results': overall_result, 'uri': request.META.get('HTTP_REFERER')})


@admin.register(models.Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ('application', 'education_type', 'specialization', 'avg_score', 'is_ended')
    list_filter = ('education_type', 'avg_score', 'is_ended')


@admin.register(models.File)
class FileAdmin(admin.ModelAdmin):
    list_display = ('member', 'file_name', 'create_date', 'is_template',)
    list_filter = ('member', 'file_name', 'create_date')


@admin.register(models.Competence)
class CompetenceAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_directions', 'is_estimated')
    list_filter = ('name', 'is_estimated')

    def get_directions(self, obj):
        return ', '.join([d.name for d in obj.directions.all()])

    get_directions.short_description = 'Направления'


@admin.register(models.Direction)
class DirectionAdmin(admin.ModelAdmin):
    list_display = ('name',)
    list_filter = ('name',)


@admin.register(models.ApplicationCompetencies)
class ApplicationCompetenciesAdmin(admin.ModelAdmin):
    list_display = ('application', 'competence', 'level',)
    list_filter = ('application', 'competence', 'level',)


@admin.register(models.ApplicationNote)
class ApplicationNoteAdmin(admin.ModelAdmin):
    list_display = ('application', 'author', 'text', 'get_affiliations')
    list_filter = ('application', 'author')

    def get_affiliations(self, obj):
        return '; '.join([d.__str__() for d in obj.affiliations.all()])

    get_affiliations.short_description = 'Взводы'


@admin.register(models.Universities)
class UniversitiesAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'rating_place')
    search_fields = ('name',)


@admin.register(models.ApplicationScores)
class ApplicationScoresAdmin(admin.ModelAdmin):
    list_display = ('application', 'a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7')
    list_filter = ('application', 'a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7')


@admin.register(models.AdditionField)
class AdditionFieldAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(models.AdditionFieldApp)
class AdditionFieldAppAdmin(admin.ModelAdmin):
    list_display = ('addition_field', 'application', 'value')


@admin.register(models.Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(models.MilitaryCommissariat)
class MilitaryCommissariatAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject',)


class ApplicationInlineAdmin(admin.TabularInline):
    model = models.Application


@admin.register(models.WorkGroup)
class WorkGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'affiliation', 'description', 'get_applications')
    list_filter = ('name', 'affiliation')

    def get_applications(self, obj):
        return '; '.join([d.__str__() for d in obj.application.all()])

    get_applications.short_description = 'Взводы'

    inlines = [ApplicationInlineAdmin]


@admin.register(models.AppsViewedByMaster)
class AppsViewedByMasterAdmin(admin.ModelAdmin):
    list_display = ('member', 'application')
