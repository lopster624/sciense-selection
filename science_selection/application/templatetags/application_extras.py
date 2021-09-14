from django import template

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
