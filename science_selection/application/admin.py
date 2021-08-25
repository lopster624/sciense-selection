from django.contrib import admin

from . import models as model


@admin.register(model.Application)
class ApplicationAdmin(admin.ModelAdmin):
    pass


@admin.register(model.Education)
class EducationAdmin(admin.ModelAdmin):
    pass


@admin.register(model.File)
class FileAdmin(admin.ModelAdmin):
    pass


@admin.register(model.Competence)
class CompetenceAdmin(admin.ModelAdmin):
    pass


@admin.register(model.Direction)
class DirectionAdmin(admin.ModelAdmin):
    pass


@admin.register(model.AdditionField)
class AdditionFieldAdmin(admin.ModelAdmin):
    pass


@admin.register(model.AdditionFieldApp)
class AdditionFieldAppAdmin(admin.ModelAdmin):
    pass


@admin.register(model.ApplicationCompetencies)
class ApplicationCompetenciesAdmin(admin.ModelAdmin):
    pass
