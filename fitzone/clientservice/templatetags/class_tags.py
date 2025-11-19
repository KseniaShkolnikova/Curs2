from django import template

register = template.Library()

@register.filter
def duration_display(minutes):
    """Отображает длительность в формате 'X ч Y мин'"""
    try:
        # Обрабатываем разные типы входных данных
        if minutes is None:
            return "60 мин"
            
        if isinstance(minutes, (int, float)):
            total_minutes = minutes
        elif isinstance(minutes, str) and minutes.strip():
            total_minutes = float(minutes)
        else:
            return "60 мин"
        
        hours = int(total_minutes // 60)
        mins = int(total_minutes % 60)
        
        if hours > 0 and mins > 0:
            return f"{hours} ч {mins} мин"
        elif hours > 0:
            return f"{hours} ч"
        else:
            return f"{mins} мин"
            
    except (ValueError, TypeError, AttributeError):
        return "60 мин"

@register.filter
def format_time(datetime_obj):
    """Форматирует время в читаемый вид"""
    if datetime_obj:
        return datetime_obj.strftime("%H:%M")
    return ""