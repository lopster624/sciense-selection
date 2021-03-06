from django import template

from account.models import Affiliation
from application.models import ApplicationNote, Education, Application, AppsViewedByMaster
from application.utils import is_booked_our

register = template.Library()


@register.filter(name='getkey')
def get_key(value, arg):
    return value.get(arg, None)


@register.filter(name='intersections')
def get_intersections(value, arg):
    if value and arg:
        return bool(list(set(value) & set(arg)))
    return False


@register.inclusion_tag('application/tags/modal_window_tag.html')
def get_modal_window(text, action_link, title, link_id):
    """Рендерит шаблон универсального модального окна для подтверждения удаления."""
    return {'text': text, 'action_link': action_link, 'title': title, 'link_id': link_id, }


@register.simple_tag
def vals_to_str(*vals):
    """Возвращает все переданные переменные в виде одной строки"""
    return ''.join(map(str, vals))


@register.simple_tag
def get_object_number(page, per_page, is_paginated, counter):
    """Возвращает номер записи учитывая пагинацию"""
    if not is_paginated:
        return counter
    return (page-1) * per_page + counter


@register.simple_tag
def init_field(field, init):
    """Инициализирует поле значением из init и возвращает его"""
    field.initial = init
    return field


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
    """
    Рендерит кнопку блокирования редактирования анкеты,
    если данная анкета отобрана в направления текущего пользователя
    """
    if is_booked_our(pk=application.id, user=user):
        return {'user_app': application}
    return {}


@register.inclusion_tag('application/tags/is_unsuitable_switch_tag.html')
def get_is_unsuitable_switch(application):
    """
    Рендерит кнопку переключения анкеты (подходящая/неподходящая)
    """
    return {'user_app': application}


@register.simple_tag
def get_education_type_name(letter):
    if not letter:
        return ''
    return next(name for ed_type, name in Education.education_program if ed_type == letter)


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.simple_tag
def get_test_result(test_id, results):
    """
    :param test_id: id экземпляра Test
    :param results: queryset из всех результатов заявки
    :return: результат пройденного теста или '-', если тест не был пройден
    """
    for test_result in results:
        if test_result.test.id == test_id:
            return test_result.result
    return '-'


@register.simple_tag
def count_number_apps_not_viewed(user):
    total_apps = Application.objects.count()
    num_apps_viewed = AppsViewedByMaster.objects.filter(member=user.member).count()
    return total_apps - num_apps_viewed
