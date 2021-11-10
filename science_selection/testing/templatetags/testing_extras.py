from django import template


register = template.Library()


@register.inclusion_tag('testing/tags/delete_test_tag.html')
def get_delete_test_modal(test):
    return {'test': test}


@register.inclusion_tag('testing/tags/exclude_test_tag.html')
def get_exclude_test_modal(test, direction):
    return {'test': test, 'direction': direction}


@register.filter()
def to_str(value):
    return str(value)
