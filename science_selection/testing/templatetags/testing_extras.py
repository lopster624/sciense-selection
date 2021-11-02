from django import template


register = template.Library()


@register.inclusion_tag('testing/tags/delete_test_tag.html')
def get_delete_test_modal(test):
    return {'test': test}
