from django import template


register = template.Library()


@register.filter(name='getkey')
def get_key(value, arg):
    return value[arg]
