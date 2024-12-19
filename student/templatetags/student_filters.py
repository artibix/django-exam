# student/templatetags/student_filters.py

from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """自定义模板过滤器，用于字典查找"""
    return dictionary.get(key, '')
