from django import template

register = template.Library()


@register.filter(name='split')
def split_string(value, delimiter=','):
    if not value:
        return []
    return [s.strip() for s in value.split(delimiter) if s.strip()]
