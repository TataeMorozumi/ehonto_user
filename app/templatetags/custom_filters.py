# app/templatetags/custom_filters.py

from django import template
from app.models import Favorite

register = template.Library()

@register.filter
def is_favorited(child, book):
    return Favorite.objects.filter(child=child, book=book).exists()

@register.filter
def get_item(dictionary, key):
    """辞書からキーで値を取得するフィルター"""
    try:
        return dictionary.get(key)
    except AttributeError:
        return None

@register.filter
def dict_items(value):
    if isinstance(value, dict):
        return value.items()
    return []
