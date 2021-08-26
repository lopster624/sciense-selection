from django.contrib import admin

from . import models


@admin.register(models.Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('role', 'user', 'father_name', 'phone', 'get_affiliations')
    list_filter = ('role',)

    def get_affiliations(self, obj):
        return ', '.join([d.name for d in obj.affiliations.all()])


@admin.register(models.Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('role_name',)
    list_filter = ('role_name',)


@admin.register(models.Affiliation)
class AffiliationAdmin(admin.ModelAdmin):
    list_display = ('direction', 'company', 'platoon')
    list_filter = ('direction', 'company', 'platoon')


@admin.register(models.Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_type', 'master', 'slave',)
    list_filter = ('booking_type', 'master', 'slave',)


@admin.register(models.BookingType)
class BookingTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    list_filter = ('name',)


@admin.register(models.ActivationLink)
class ActivationLinkAdmin(admin.ModelAdmin):
    pass
