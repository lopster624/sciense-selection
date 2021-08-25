from django.contrib import admin

from . import models as model


@admin.register(model.Member)
class ApplicationAdmin(admin.ModelAdmin):
    pass


@admin.register(model.Role)
class ApplicationAdmin(admin.ModelAdmin):
    pass


@admin.register(model.Affiliation)
class ApplicationAdmin(admin.ModelAdmin):
    pass
