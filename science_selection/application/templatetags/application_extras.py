from django import template

from account.models import Affiliation
from application.models import ApplicationNote, Education
from application.utils import check_booking_our
from utils.constants import MASTER_ROLE_NAME

register = template.Library()


@register.filter(name='getkey')
def get_key(value, arg):
    return value[arg]


@register.filter(name='intersections')
def get_intersections(value, arg):
    if value and arg:
        return True if list(set(value) & set(arg)) else False
    return False


@register.inclusion_tag('application/tags/delete_competence_tag.html')
def get_delete_competence_modal(competence, direction):
    return {'comp': competence, 'direction': direction}


@register.inclusion_tag('application/tags/application_note_tag.html')
def get_application_note(application, user):
    master_affiliations = Affiliation.objects.filter(member=user.member)
    other_notes = ApplicationNote.objects.filter(application=application, affiliations__in=master_affiliations,
                                                 ).exclude(author=user.member).distinct()
    app_note = ApplicationNote.objects.filter(application=application, affiliations__in=master_affiliations,
                                              author=user.member).distinct()
    return {'app_note': app_note.first(), 'application': application, 'other_notes': other_notes}


@register.inclusion_tag('application/tags/is_final_switch_tag.html')
def get_is_final_switch(application, user):
    if user.member.role.role_name != MASTER_ROLE_NAME or not check_booking_our(pk=application.id, user=user):
        return {}
    return {'user_app': application}


@register.simple_tag
def get_education_type_name(letter):
    return next(name for ed_type, name in Education.education_program if ed_type == letter)
