from django import template
from django.utils import timezone
from datetime import timedelta

register = template.Library()

@register.simple_tag
def duration_display(days):
    """Конвертирует дни в читаемый формат с годами, месяцами и днями"""
    days = int(days)
    
    years = days // 365
    remaining_days = days % 365
    months = remaining_days // 30
    remaining_days = remaining_days % 30
    
    parts = []
    
    if years > 0:
        if years == 1:
            parts.append("1 год")
        elif 2 <= years <= 4:
            parts.append(f"{years} года")
        else:
            parts.append(f"{years} лет")
    
    if months > 0:
        if months == 1:
            parts.append("1 месяц")
        elif 2 <= months <= 4:
            parts.append(f"{months} месяца")
        else:
            parts.append(f"{months} месяцев")
    
    if remaining_days > 0:
        if remaining_days == 1:
            parts.append("1 день")
        elif 2 <= remaining_days <= 4:
            parts.append(f"{remaining_days} дня")
        else:
            parts.append(f"{remaining_days} дней")
    
    # Если срок 0 дней (хотя это маловероятно)
    if not parts:
        return "0 дней"
    
    return " ".join(parts)

@register.filter
def days_remaining(subscription):
    """Возвращает количество оставшихся дней абонемента"""
    if not subscription.is_active:
        return 0
        
    end_date = subscription.startdate + timedelta(days=subscription.subscriptiontype.durationdays)
    remaining = (end_date - timezone.now().date()).days
    return max(0, remaining)

@register.filter
def should_show_renewal(subscription):
    """Показывать ли кнопку продления (осталось 1 день или меньше)"""
    if not subscription.is_active:
        return False
        
    end_date = subscription.startdate + timedelta(days=subscription.subscriptiontype.durationdays)
    remaining = (end_date - timezone.now().date()).days
    return remaining <= 1

@register.filter
def is_expiring_soon(subscription):
    """Абонемент истекает скоро (менее 3 дней)"""
    if not subscription.is_active:
        return False
        
    end_date = subscription.startdate + timedelta(days=subscription.subscriptiontype.durationdays)
    remaining = (end_date - timezone.now().date()).days
    return 1 <= remaining <= 3

@register.filter
def add_days(date, days):
    """Добавляет дни к дате"""
    return date + timedelta(days=int(days))

@register.filter
def subscription_status_class(subscription):
    """Возвращает CSS класс для статуса абонемента"""
    if not subscription.is_active:
        return "inactive_state_ui"
    
    end_date = subscription.startdate + timedelta(days=subscription.subscriptiontype.durationdays)
    remaining = (end_date - timezone.now().date()).days
    
    # Проверяем, истек ли абонемент
    if remaining <= 0:
        return "inactive_state_ui"
    
    if remaining <= 3:
        return "expiring-soon"
    else:
        return "active_state_ui"

@register.filter
def subscription_status_text(subscription):
    """Возвращает текст статуса абонемента"""
    if not subscription.is_active:
        return "НЕАКТИВЕН"
    
    end_date = subscription.startdate + timedelta(days=subscription.subscriptiontype.durationdays)
    remaining = (end_date - timezone.now().date()).days
    
    if remaining <= 0:
        return "ИСТЕК"
    elif remaining == 1:
        return "ЗАВТРА ИСТЕКАЕТ"
    elif remaining <= 3:
        return f"СКОРО ИСТЕКАЕТ ({remaining} д.)"
    else:
        return f"АКТИВЕН ({remaining} д.)"

@register.filter
def subscription_status_icon(subscription):
    """Возвращает иконку для статуса абонемента"""
    if not subscription.is_active:
        return "fas fa-clock"
    
    end_date = subscription.startdate + timedelta(days=subscription.subscriptiontype.durationdays)
    remaining = (end_date - timezone.now().date()).days
    
    if remaining <= 0:
        return "fas fa-times-circle"
    elif remaining <= 3:
        return "fas fa-exclamation-triangle"
    else:
        return "fas fa-bolt"

@register.filter
def can_cancel_subscription(subscription):
    """Можно ли отменить абонемент"""
    if not subscription.is_active:
        return False
    
    # Можно отменять только активные абонементы
    # Можно добавить дополнительные условия, например:
    # - нельзя отменять в день истечения
    # - нельзя отменять если прошло больше половины срока и т.д.
    return True

@register.filter
def subscription_progress_percentage(subscription):
    """Возвращает процент использования абонемента"""
    if not subscription.is_active:
        return 100
    
    total_days = subscription.subscriptiontype.durationdays
    days_passed = (timezone.now().date() - subscription.startdate).days
    percentage = min(100, max(0, (days_passed / total_days) * 100))
    return int(percentage)

@register.filter
def is_subscription_expired(subscription):
    """Проверяет, истек ли абонемент"""
    if not subscription.is_active:
        return True
    
    end_date = subscription.startdate + timedelta(days=subscription.subscriptiontype.durationdays)
    return timezone.now().date() > end_date

@register.filter
def subscription_days_used(subscription):
    """Возвращает количество использованных дней абонемента"""
    if not subscription.is_active:
        return subscription.subscriptiontype.durationdays
    
    days_used = (timezone.now().date() - subscription.startdate).days
    return min(subscription.subscriptiontype.durationdays, max(0, days_used))

@register.filter
def subscription_days_left(subscription):
    """Возвращает количество оставшихся дней абонемента"""
    if not subscription.is_active:
        return 0
    
    end_date = subscription.startdate + timedelta(days=subscription.subscriptiontype.durationdays)
    days_left = (end_date - timezone.now().date()).days
    return max(0, days_left)