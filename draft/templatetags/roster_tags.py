from django import template

register = template.Library()

@register.filter
def make_range(value):
    """Returns a range from 0 to value"""
    return range(int(value))

@register.filter
def upper(value):
    return str(value).upper()

@register.filter
def dict_key(d, key):
    """Access dictionary values by key in templates"""
    return d.get(key, [])