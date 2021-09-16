from django import template

from account.models import Affiliation
from application.models import ApplicationNote

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
def get_delete_competence_modal(application, user):
    master_affiliations = Affiliation.objects.filter(member=user.member)
    app_note = ApplicationNote.objects.filter(application=application, affiliations__in=master_affiliations).first()
    print(app_note)
    return {'app_note': app_note, 'application': application}
