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
