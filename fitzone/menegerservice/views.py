from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.http import HttpResponse
from datetime import datetime, timedelta
import csv
import io
from clientservice.models import Payments, Subscriptions, SubscriptionTypes, ClassClient
from .forms import SubscriptionTypeForm, ReportFilterForm

@login_required
def manager_home(request):
    """Главная страница менеджера"""
    if not request.user.groups.filter(name='Менеджер по продажам').exists():
        messages.error(request, 'Доступ только для менеджеров')
        return redirect('home')
    
    today = timezone.now()
    first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    monthly_payments = Payments.objects.filter(
        paymentdate__gte=first_day_of_month
    ).select_related('subscription', 'classclient', 'classclient__user', 'classclient__user__userprofile')
    
    total_revenue = monthly_payments.aggregate(total=Sum('price'))['total'] or 0
    subscription_revenue = monthly_payments.filter(subscription__isnull=False).aggregate(total=Sum('price'))['total'] or 0
    classes_revenue = monthly_payments.filter(classclient__isnull=False).aggregate(total=Sum('price'))['total'] or 0
    active_subscriptions_count = Subscriptions.objects.filter(is_active=True).count()
    recent_payments = monthly_payments.order_by('-paymentdate')[:10]
    
    popular_subscriptions_data = SubscriptionTypes.objects.annotate(
        sales_count=Count('subscriptions__payments', 
                         filter=Q(subscriptions__payments__paymentdate__gte=first_day_of_month)),
        total_revenue=Sum('subscriptions__payments__price',
                         filter=Q(subscriptions__payments__paymentdate__gte=first_day_of_month))
    ).filter(sales_count__gt=0).order_by('-sales_count')[:5]
    
    popular_subscriptions = []
    for sub_type in popular_subscriptions_data:
        popular_subscriptions.append({
            'name': sub_type.name,
            'price': sub_type.price,
            'sales_count': sub_type.sales_count,
            'total_revenue': sub_type.total_revenue or 0
        })
    
    month_names = {
        1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель',
        5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август',
        9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
    }
    current_month_name = f"{month_names[today.month]} {today.year}"
    
    context = {
        'total_revenue': total_revenue,
        'subscription_revenue': subscription_revenue,
        'classes_revenue': classes_revenue,
        'active_subscriptions_count': active_subscriptions_count,
        'recent_payments': recent_payments,
        'popular_subscriptions': popular_subscriptions,
        'current_month': current_month_name
    }
    
    return render(request, 'manager_home.html', context)

@login_required
def create_subscription(request):
    """Создание нового типа абонемента"""
    if not request.user.groups.filter(name='Менеджер по продажам').exists():
        messages.error(request, 'Доступ только для менеджеров')
        return redirect('home')
    
    if request.method == 'POST':
        form = SubscriptionTypeForm(request.POST)
        if form.is_valid():
            subscription = form.save()
            messages.success(request, f'Абонемент "{subscription.name}" успешно создан!')
            return redirect('menegerservice:subscriptions_list')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = SubscriptionTypeForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'create_subscription.html', context)


import json


import json
from datetime import datetime, timedelta
from django.db.models.functions import TruncDate

@login_required
def reports(request):
    """Страница отчетов с фильтрацией по периодами и графиком"""
    if not request.user.groups.filter(name='Менеджер по продажам').exists():
        messages.error(request, 'Доступ только для менеджеров')
        return redirect('home')
    
    form = ReportFilterForm(request.GET or None)
    report_data = None
    summary = None
    daily_revenue_data = None
    daily_revenue_labels = '[]'
    daily_revenue_values = '[]'
    export_params = request.GET.urlencode()
    
    if form.is_valid():
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']
        report_type = form.cleaned_data['report_type']
        
        # Фильтруем платежи по дате
        payments = Payments.objects.filter(
            paymentdate__date__gte=start_date,
            paymentdate__date__lte=end_date
        ).select_related('subscription', 'classclient', 'classclient__user', 'classclient__user__userprofile')
        
        if report_type == 'subscriptions':
            payments = payments.filter(subscription__isnull=False)
        elif report_type == 'classes':
            payments = payments.filter(classclient__isnull=False)
        
        # ДАННЫЕ ДЛЯ ГРАФИКА - ИСПРАВЛЕННАЯ ЛОГИКА
        # Создаем полный диапазон дат для избежания пропусков
        date_range = []
        current_date = start_date
        while current_date <= end_date:
            date_range.append(current_date)
            current_date += timedelta(days=1)
        
        # Получаем доход по дням
        daily_revenue_dict = {}
        daily_payments = payments.annotate(
            payment_date=TruncDate('paymentdate')
        ).values('payment_date').annotate(
            daily_total=Sum('price')
        ).order_by('payment_date')
        
        # Заполняем словарь с доходами по дням
        for payment_day in daily_payments:
            date_key = payment_day['payment_date'].strftime('%d.%m')
            daily_revenue_dict[date_key] = float(payment_day['daily_total'])
        
        # Создаем массивы для графика, включая дни с нулевым доходом
        daily_revenue_labels_list = []
        daily_revenue_values_list = []
        
        for single_date in date_range:
            date_str = single_date.strftime('%d.%m')
            daily_revenue_labels_list.append(date_str)
            # Используем доход из словаря или 0, если данных нет
            daily_revenue_values_list.append(daily_revenue_dict.get(date_str, 0.0))
        
        # Преобразуем в JSON-совместимые строки
        daily_revenue_labels = json.dumps(daily_revenue_labels_list)
        daily_revenue_values = json.dumps(daily_revenue_values_list)
        
        # Устанавливаем флаг наличия данных для графика
        daily_revenue_data = len(daily_revenue_labels_list) > 0
        
        # Остальная логика формирования отчета...
        if report_type == 'subscriptions':
            subscription_payments = payments.filter(subscription__isnull=False)
            report_data = []
            
            for payment in subscription_payments:
                report_data.append({
                    'date': payment.paymentdate,
                    'type': 'Абонемент',
                    'name': payment.subscription.subscriptiontype.name,
                    'client': payment.subscription.user.userprofile.full_name or payment.subscription.user.username,
                    'amount': payment.price,
                    'duration': f"{payment.subscription.subscriptiontype.durationdays} дней"
                })
            
            total_revenue = subscription_payments.aggregate(total=Sum('price'))['total'] or 0
            total_sales = subscription_payments.count()
            avg_revenue = total_revenue / total_sales if total_sales > 0 else 0
            
            summary = {
                'total_revenue': total_revenue,
                'total_sales': total_sales,
                'avg_revenue': round(avg_revenue, 2),
                'period': f"{start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}",
                'report_type': 'по абонементам'
            }
            
        elif report_type == 'classes':
            class_payments = payments.filter(classclient__isnull=False)
            report_data = []
            
            for payment in class_payments:
                report_data.append({
                    'date': payment.paymentdate,
                    'type': 'Тренировка',
                    'name': payment.classclient.class_id.name,
                    'client': payment.classclient.user.userprofile.full_name or payment.classclient.user.username,
                    'amount': payment.price,
                    'duration': None
                })
            
            total_revenue = class_payments.aggregate(total=Sum('price'))['total'] or 0
            total_sales = class_payments.count()
            avg_revenue = total_revenue / total_sales if total_sales > 0 else 0
            
            summary = {
                'total_revenue': total_revenue,
                'total_sales': total_sales,
                'avg_revenue': round(avg_revenue, 2),
                'period': f"{start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}",
                'report_type': 'по тренировкам'
            }
            
        else:  # combined report
            report_data = []
            
            for payment in payments:
                if payment.subscription:
                    item = {
                        'date': payment.paymentdate,
                        'type': 'Абонемент',
                        'name': payment.subscription.subscriptiontype.name,
                        'client': payment.subscription.user.userprofile.full_name or payment.subscription.user.username,
                        'amount': payment.price,
                        'duration': f"{payment.subscription.subscriptiontype.durationdays} дней"
                    }
                else:
                    item = {
                        'date': payment.paymentdate,
                        'type': 'Тренировка',
                        'name': payment.classclient.class_id.name,
                        'client': payment.classclient.user.userprofile.full_name or payment.classclient.user.username,
                        'amount': payment.price,
                        'duration': None
                    }
                report_data.append(item)
            
            total_revenue = payments.aggregate(total=Sum('price'))['total'] or 0
            total_sales = payments.count()
            subscription_sales = payments.filter(subscription__isnull=False).count()
            class_sales = payments.filter(classclient__isnull=False).count()
            avg_revenue = total_revenue / total_sales if total_sales > 0 else 0
            
            summary = {
                'total_revenue': total_revenue,
                'total_sales': total_sales,
                'subscription_sales': subscription_sales,
                'class_sales': class_sales,
                'avg_revenue': round(avg_revenue, 2),
                'period': f"{start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}",
                'report_type': 'общий'
            }
    
    context = {
        'form': form,
        'report_data': report_data,
        'summary': summary,
        'daily_revenue_data': daily_revenue_data,
        'daily_revenue_labels': daily_revenue_labels,
        'daily_revenue_values': daily_revenue_values,
        'export_params': export_params,
    }
    
    return render(request, 'reports.html', context)


@login_required
def export_reports_csv(request):
    """Экспорт отчетов в CSV"""
    if not request.user.groups.filter(name='Менеджер по продажам').exists():
        messages.error(request, 'Доступ только для менеджеров')
        return redirect('home')
    
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    report_type = request.GET.get('report_type', 'combined')
    
    if not start_date or not end_date:
        messages.error(request, 'Не указаны даты для экспорта')
        return redirect('menegerservice:reports')
    
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, 'Неверный формат даты')
        return redirect('menegerservice:reports')
    
    payments = Payments.objects.filter(
        paymentdate__date__gte=start_date,
        paymentdate__date__lte=end_date
    ).select_related('subscription', 'classclient', 'classclient__user', 'classclient__user__userprofile')
    
    if report_type == 'subscriptions':
        payments = payments.filter(subscription__isnull=False)
    elif report_type == 'classes':
        payments = payments.filter(classclient__isnull=False)
    
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="report_{start_date}_{end_date}.csv"'
    
    # Добавляем BOM для корректного отображения кириллицы в Excel
    response.write('\ufeff')
    
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Дата', 'Тип', 'Название', 'Клиент', 'Сумма (₽)', 'Длительность'])
    
    for payment in payments:
        if payment.subscription:
            row = [
                payment.paymentdate.strftime('%d.%m.%Y %H:%M'),
                'Абонемент',
                payment.subscription.subscriptiontype.name,
                payment.subscription.user.userprofile.full_name or payment.subscription.user.username,
                str(payment.price).replace('.', ','),
                f"{payment.subscription.subscriptiontype.durationdays} дней"
            ]
        else:
            row = [
                payment.paymentdate.strftime('%d.%m.%Y %H:%M'),
                'Тренировка',
                payment.classclient.class_id.name,
                payment.classclient.user.userprofile.full_name or payment.classclient.user.username,
                str(payment.price).replace('.', ','),
                'Разовое занятие'
            ]
        writer.writerow(row)
    
    return response

from django.template.loader import render_to_string
from django.http import HttpResponse
import io

@login_required
def export_reports_pdf(request):
    """Экспорт отчетов в PDF с полным оформлением"""
    if not request.user.groups.filter(name='Менеджер по продажам').exists():
        messages.error(request, 'Доступ только для менеджеров')
        return redirect('home')
    
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    report_type = request.GET.get('report_type', 'combined')
    
    if not start_date or not end_date:
        messages.error(request, 'Не указаны даты для экспорта')
        return redirect('menegerservice:reports')
    
    try:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, 'Неверный формат даты')
        return redirect('menegerservice:reports')
    
    # Получаем данные
    payments = Payments.objects.filter(
        paymentdate__date__gte=start_date_obj,
        paymentdate__date__lte=end_date_obj
    ).select_related('subscription', 'classclient', 'classclient__user', 'classclient__user__userprofile')
    
    if report_type == 'subscriptions':
        payments = payments.filter(subscription__isnull=False)
    elif report_type == 'classes':
        payments = payments.filter(classclient__isnull=False)
    
    # Статистика
    total_revenue = payments.aggregate(total=Sum('price'))['total'] or 0
    total_sales = payments.count()
    subscription_sales = payments.filter(subscription__isnull=False).count()
    class_sales = payments.filter(classclient__isnull=False).count()
    avg_revenue = total_revenue / total_sales if total_sales > 0 else 0
    
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib import colors
        import os
        
        # Регистрируем шрифт
        try:
            font_paths = [
                'C:/Windows/Fonts/arial.ttf',
                'C:/Windows/Fonts/tahoma.ttf', 
                '/usr/share/fonts/truetype/freefont/FreeSans.ttf',
                '/Library/Fonts/Arial.ttf',
            ]
            
            font_found = False
            for font_path in font_paths:
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont('Arial', font_path))
                    pdfmetrics.registerFont(TTFont('Arial-Bold', font_path))
                    font_name = 'Arial'
                    font_found = True
                    break
            
            if not font_found:
                font_name = 'Helvetica'
                
        except:
            font_name = 'Helvetica'
        
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        page_number = 1
        
        # Верхний колонтитул
        def draw_header():
            p.setFillColor(colors.HexColor('#8a2be2'))
            p.rect(0, height-60, width, 60, fill=1, stroke=0)
            p.setFillColor(colors.white)
            p.setFont(font_name + '-Bold', 16)
            p.drawString(50, height-35, "ООО 'FITZONE'")
            p.setFont(font_name, 12)
            p.drawString(50, height-50, "Фитнес-центр премиум-класса")
            
            p.setFillColor(colors.black)
            p.setFont(font_name + '-Bold', 20)
            p.drawCentredString(width/2, height-100, "ФИНАНСОВЫЙ ОТЧЕТ")
        
        # Нижний колонтитул
        def draw_footer():
            p.setFillColor(colors.grey)
            p.setFont(font_name, 8)
            p.drawString(50, 30, f"ООО 'FitZone', ИНН 1234567890, г. Москва, ул. Фитнесная, 1")
            p.drawString(50, 20, f"Отчет сгенерирован: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
            p.drawString(500, 20, f"Страница {page_number}")
        
        # Функция для получения ФИО в формате "И.И. Иванов"
        def get_formatted_fio(user):
            profile = getattr(user, 'userprofile', None)
            if profile:
                # Форматируем ФИО: И.И. Иванов
                parts = []
                if profile.firstname:
                    parts.append(f"{profile.firstname[0]}." if profile.firstname else '')
                if profile.middlename:
                    parts.append(f"{profile.middlename[0]}." if profile.middlename else '')
                if profile.lastname:
                    parts.append(profile.lastname)
                
                formatted_fio = ' '.join(parts).strip()
                if formatted_fio:
                    return formatted_fio
            
            # Если нет профиля, используем имя пользователя
            return user.username
        
        # Функция для получения полного ФИО
        def get_full_fio(user):
            profile = getattr(user, 'userprofile', None)
            if profile and profile.full_name:
                return profile.full_name
            return user.username
        
        # Функция для переноса текста
        def draw_wrapped_text(canvas, text, x, y, max_width, max_lines=2, font_size=9):
            if not text:
                return 1
                
            words = text.split(' ')
            lines = []
            current_line = []
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                test_width = canvas.stringWidth(test_line, font_name, font_size)
                
                if test_width <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
                    
                    if len(lines) >= max_lines:
                        break
            
            if current_line and len(lines) < max_lines:
                lines.append(' '.join(current_line))
            
            # Если текст не влез, добавляем многоточие
            if len(lines) == max_lines and len(' '.join(current_line)) > 0:
                last_line = lines[-1]
                while last_line and canvas.stringWidth(last_line + '...', font_name, font_size) > max_width:
                    last_line = last_line[:-1]
                lines[-1] = last_line + '...'
            
            # Рисуем линии
            for i, line in enumerate(lines):
                canvas.drawString(x, y - (i * 12), line)
            
            return len(lines)
        
        # Рисуем шапку
        draw_header()
        
        # Информация об отчете
        p.setFont(font_name, 12)
        p.drawString(50, height-130, f"Период отчета: {start_date_obj.strftime('%d.%m.%Y')} - {end_date_obj.strftime('%d.%m.%Y')}")
        
        report_type_text = {
            'combined': 'Общий отчет по всем продажам',
            'subscriptions': 'Отчет по продажам абонементов', 
            'classes': 'Отчет по продажам тренировок'
        }.get(report_type, 'Общий отчет')
        
        p.drawString(50, height-150, f"Тип отчета: {report_type_text}")
        
        # Ответственный с полным ФИО
        responsible_fio = get_full_fio(request.user)
        p.drawString(50, height-170, f"Ответственный: {responsible_fio}")
        
        # Разделительная линия
        p.setStrokeColor(colors.grey)
        p.line(50, height-180, width-50, height-180)
        
        # Сводная статистика с красивым оформлением
        y_position = height - 220
        
        p.setFillColor(colors.HexColor('#f8f9fa'))
        p.rect(50, y_position-140, width-100, 140, fill=1, stroke=0)
        p.setFillColor(colors.black)
        
        p.setFont(font_name + '-Bold', 16)
        p.drawString(60, y_position-30, "СВОДНАЯ СТАТИСТИКА")
        
        p.setFont(font_name, 12)
        stats_y = y_position - 60
        
        # Статистика в две колонки
        stats_left = [
            f"Общий доход: {total_revenue:,.2f} ₽".replace(',', ' '),
            f"Всего продаж: {total_sales}",
            f"Средний чек: {avg_revenue:,.2f} ₽".replace(',', ' '),
        ]
        
        stats_right = []
        if report_type == 'combined':
            stats_right = [
                f"Продажи абонементов: {subscription_sales}",
                f"Продажи тренировок: {class_sales}",
            ]
        
        for i, stat in enumerate(stats_left):
            p.drawString(70, stats_y - (i * 25), stat)
        
        for i, stat in enumerate(stats_right):
            p.drawString(300, stats_y - (i * 25), stat)
        
        # Детализация продаж
        y_position = y_position - 180
        
        if payments.exists():
            p.setFont(font_name + '-Bold', 16)
            p.drawString(50, y_position, "ДЕТАЛИЗАЦИЯ ПРОДАЖ")
            
            # Заголовки таблицы с ОПТИМИЗИРОВАННЫМИ ШИРИНАМИ
            y_position -= 30
            p.setFillColor(colors.HexColor('#8a2be2'))
            p.rect(50, y_position-25, width-100, 25, fill=1, stroke=0)
            p.setFillColor(colors.white)
            p.setFont(font_name + '-Bold', 9)
            
            # ОПТИМИЗИРОВАННЫЕ ЗАГОЛОВКИ КОЛОНОК
            p.drawString(60, y_position-15, "Дата")           # 60 (60px ширина)
            p.drawString(120, y_position-15, "Тип")           # 120 (50px ширина - УМЕНЬШЕНО)
            p.drawString(170, y_position-15, "Название")      # 170 (180px ширина - УВЕЛИЧЕНО)
            p.drawString(350, y_position-15, "Клиент")        # 350 (80px ширина - УМЕНЬШЕНО)
            p.drawString(430, y_position-15, "Сумма")         # 430 (60px ширина)
            p.drawString(490, y_position-15, "Длит.")         # 490 (40px ширина)
            
            y_position -= 35
            p.setFillColor(colors.black)
            p.setFont(font_name, 8)
            
            for i, payment in enumerate(payments):
                if y_position < 100:
                    # Новая страница
                    draw_footer()
                    p.showPage()
                    page_number += 1
                    draw_header()
                    y_position = height - 220
                    
                    # Повторяем заголовки таблицы
                    p.setFillColor(colors.HexColor('#8a2be2'))
                    p.rect(50, y_position-25, width-100, 25, fill=1, stroke=0)
                    p.setFillColor(colors.white)
                    p.setFont(font_name + '-Bold', 9)
                    p.drawString(60, y_position-15, "Дата")
                    p.drawString(120, y_position-15, "Тип")
                    p.drawString(170, y_position-15, "Название")
                    p.drawString(350, y_position-15, "Клиент")
                    p.drawString(430, y_position-15, "Сумма")
                    p.drawString(490, y_position-15, "Длит.")
                    
                    y_position -= 35
                    p.setFillColor(colors.black)
                    p.setFont(font_name, 8)
                
                # Чередование цвета строк
                if i % 2 == 0:
                    p.setFillColor(colors.HexColor('#f8f9fa'))
                    p.rect(50, y_position-15, width-100, 15, fill=1, stroke=0)
                    p.setFillColor(colors.black)
                
                # Получаем данные о платеже
                if payment.subscription:
                    payment_type = 'Абонемент'
                    name = payment.subscription.subscriptiontype.name
                    # Получаем ФИО клиента в формате "И.И. Иванов"
                    client_fio = get_formatted_fio(payment.subscription.user)
                    amount = f"{payment.price:,.0f} ₽".replace(',', ' ')
                    duration = f"{payment.subscription.subscriptiontype.durationdays} дн."
                    date_str = payment.paymentdate.strftime('%d.%m.%Y')
                else:
                    payment_type = 'Тренировка'
                    name = payment.classclient.class_id.name
                    # Получаем ФИО клиента в формате "И.И. Иванов"
                    client_fio = get_formatted_fio(payment.classclient.user)
                    amount = f"{payment.price:,.0f} ₽".replace(',', ' ')
                    duration = 'Разово'
                    date_str = payment.paymentdate.strftime('%d.%m.%Y')
                
                # Рисуем данные с переносами
                p.drawString(60, y_position-10, date_str)
                p.drawString(120, y_position-10, payment_type)  # Уменьшенное место для типа
                
                # Название с переносом (ширина 170px, 2 строки - УВЕЛИЧЕНО)
                name_lines = draw_wrapped_text(p, str(name), 170, y_position-10, 170, 2, 8)
                
                # Клиент с переносом (ширина 70px, 1 строка - УМЕНЬШЕНО)
                client_lines = draw_wrapped_text(p, str(client_fio), 350, y_position-10, 70, 1, 8)
                
                p.drawString(430, y_position-10, amount)
                p.drawString(490, y_position-10, duration)
                
                # Увеличиваем отступ в зависимости от количества строк
                max_lines = max(name_lines, client_lines)
                y_position -= (15 + (max_lines - 1) * 10)
                
        else:
            p.setFont(font_name, 12)
            p.drawString(50, y_position, "Нет данных за выбранный период")
            y_position -= 30
        
        # Подпись
        y_position -= 50
        p.setFont(font_name, 10)
        p.drawString(400, y_position, "_________________________")
        p.drawString(400, y_position-15, "Подпись ответственного лица")
        
        # Рисуем нижний колонтитул
        draw_footer()
        
        p.showPage()
        p.save()
        
        pdf = buffer.getvalue()
        buffer.close()
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Финансовый_отчет_{start_date}_{end_date}.pdf"'
        return response
        
    except Exception as e:
        messages.error(request, f'Ошибка генерации PDF: {str(e)}')
        return redirect('menegerservice:reports')
    

    

@login_required
def subscriptions_list(request):
    """Список всех типов абонементов"""
    if not request.user.groups.filter(name='Менеджер по продажам').exists():
        messages.error(request, 'Доступ только для менеджеров')
        return redirect('home')
    
    subscriptions = SubscriptionTypes.objects.all()
    
    return render(request, 'subscriptions_list.html', {
        'subscriptions': subscriptions
    })

# Добавьте эти views в ваш views.py

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Count

@login_required
@require_http_methods(["GET"])
def subscription_detail_json(request, subscription_id):
    """Получение данных абонемента в JSON формате"""
    print(f"DEBUG: subscription_detail_json called with subscription_id: {subscription_id}")
    
    if not request.user.groups.filter(name='Менеджер по продажам').exists():
        return JsonResponse({'success': False, 'error': 'Доступ запрещен'})
    
    try:
        subscription = get_object_or_404(SubscriptionTypes, id=subscription_id)
        print(f"DEBUG: Found subscription: {subscription.name}")
        
        subscription_data = {
            'id': subscription.id,
            'name': subscription.name,
            'description': subscription.description,
            'price': float(subscription.price),
            'durationdays': subscription.durationdays,
            'gym_access': subscription.gym_access,
            'pool_access': subscription.pool_access,
            'spa_access': subscription.spa_access,
            'locker_room': subscription.locker_room,
            'towel_service': subscription.towel_service,
            'nutrition_consultation': subscription.nutrition_consultation,
            
        }
        
        return JsonResponse({'success': True, 'subscription': subscription_data})
    except Exception as e:
        print(f"ERROR in subscription_detail_json: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})
@login_required
@require_http_methods(["GET"])
def subscription_stats(request, subscription_id):
    """Получение статистики абонемента"""
    print(f"DEBUG: subscription_stats called with subscription_id: {subscription_id}")
    
    if not request.user.groups.filter(name='Менеджер по продажам').exists():
        return JsonResponse({'success': False, 'error': 'Доступ запрещен'})
    
    try:
        subscription = get_object_or_404(SubscriptionTypes, id=subscription_id)
        
        # Активные подписки для ЭТОГО типа абонемента
        active_subscriptions_for_type = Subscriptions.objects.filter(
            subscriptiontype=subscription,
            is_active=True
        ).count()
        
        print(f"DEBUG: Active subscriptions for type {subscription_id}: {active_subscriptions_for_type}")
        
        # ИСПРАВЛЕНИЕ: возвращаем правильное поле
        return JsonResponse({
            'success': True,
            'type_active_subscriptions': active_subscriptions_for_type  # Это поле используется в JavaScript
        })
    except Exception as e:
        print(f"ERROR in subscription_stats: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})
    

    


    

@login_required
@require_http_methods(["POST"])
def edit_subscription(request, subscription_id):
    """Редактирование абонемента"""
    if not request.user.groups.filter(name='Менеджер по продажам').exists():
        return JsonResponse({'success': False, 'error': 'Доступ запрещен'})
    
    try:
        subscription = get_object_or_404(SubscriptionTypes, id=subscription_id)
        form = SubscriptionTypeForm(request.POST, instance=subscription)
        
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            errors = form.errors.as_json()
            return JsonResponse({'success': False, 'error': 'Ошибка валидации', 'errors': errors})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["POST"])
def delete_subscription(request):
    """Удаление абонемента"""
    if not request.user.groups.filter(name='Менеджер по продажам').exists():
        return JsonResponse({'success': False, 'error': 'Доступ запрещен'})
    
    try:
        subscription_id = request.POST.get('subscription_id')
        subscription = get_object_or_404(SubscriptionTypes, id=subscription_id)
        
        # Проверяем, есть ли активные подписки
        active_subscriptions = Subscriptions.objects.filter(
            subscriptiontype=subscription,
            is_active=True
        ).exists()
        
        if active_subscriptions:
            return JsonResponse({
                'success': False, 
                'error': 'Невозможно удалить абонемент с активными подписками'
            })
        
        subscription_name = subscription.name
        subscription.delete()
        
        messages.success(request, f'Абонемент "{subscription_name}" успешно удален')
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})