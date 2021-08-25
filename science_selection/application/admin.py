from django.contrib import admin

from . import models


class CompetenciesInlineAdmin(admin.TabularInline):
    model = models.Application.competencies.through


@admin.register(models.Application)
class ApplicationAdmin(admin.ModelAdmin):
    inlines = [CompetenciesInlineAdmin]
    list_display = ('member', 'draft_year', 'draft_season', 'final_score')
    list_filter = ('draft_year', 'draft_season', 'final_score')


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


@admin.register(models.Direction)
class DirectionAdmin(admin.ModelAdmin):
    list_display = ('name',)
    list_filter = ('name',)


@admin.register(models.AdditionField)
class AdditionFieldAdmin(admin.ModelAdmin):
    pass


@admin.register(models.AdditionFieldApp)
class AdditionFieldAppAdmin(admin.ModelAdmin):
    pass


@admin.register(models.ApplicationCompetencies)
class ApplicationCompetenciesAdmin(admin.ModelAdmin):
    list_display = ('application', 'competence', 'level',)
    list_filter = ('application', 'competence', 'level',)
