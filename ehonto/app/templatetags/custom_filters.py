# app/templatetags/custom_filters.py

from django import template
from app.models import Favorite

register = template.Library()

@register.filter
def is_favorited(child, book):
    return Favorite.objects.filter(child=child, book=book).exists()
@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)
@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)
