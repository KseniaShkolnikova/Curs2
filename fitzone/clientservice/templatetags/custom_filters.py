from django import template
from datetime import timedelta

register = template.Library()

@register.filter
def add_days(date, days):
    """Добавляет дни к дате"""
    try:
        return date + timedelta(days=int(days))
    except (ValueError, TypeError):
        return date