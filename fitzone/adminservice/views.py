# adminservice/views.py
from django.contrib.auth.models import User, Group
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from django.db import connection
from utils.decorators import admin_required
import os
import json
import csv
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from datetime import datetime
import subprocess
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from clientservice.models import *

# SUMMARY: Основной модуль представлений для административной панели
# Включает функции для управления пользователями, бэкапами, логами и статистикой

@admin_required
def get_database_stats(request):
    """
    SUMMARY: Получение статистики базы данных для мониторинга
    
    ОСНОВНОЕ НАЗНАЧЕНИЕ:
    - Мониторинг размера БД и количества таблиц
    - Проверка статуса подключения к базе данных
    - Предоставление метрик для админ-панели
    
    ВОЗВРАЩАЕМЫЕ ДАННЫЕ:
    - db_size: Размер базы данных в читаемом формате
    - table_count: Количество таблиц в схеме public
    - db_status: Статус подключения ('status-ok' или 'status-error')
    - db_status_text: Текстовое описание статуса
    """
    stats = {}
    
    try:
        # SUMMARY: Получение размера базы данных через системные функции PostgreSQL
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_size_pretty(pg_database_size('fitZone_DB'))")
            db_size = cursor.fetchone()[0]
            stats['db_size'] = db_size
    except:
        stats['db_size'] = "Недоступно"
    
    try:
        # SUMMARY: Подсчет количества таблиц в схеме public
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            table_count = cursor.fetchone()[0]
            stats['table_count'] = table_count
    except:
        stats['table_count'] = "Недоступно"
    
    try:
        # SUMMARY: Проверка доступности базы данных
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        stats['db_status'] = 'status-ok'
        stats['db_status_text'] = 'Подключено'
    except:
        stats['db_status'] = 'status-error'
        stats['db_status_text'] = 'Ошибка'
    
    return stats

@admin_required
@login_required
def admin_dashboard(request):
    """
    SUMMARY: Главная панель администратора с ключевыми метриками системы
    
    ОСНОВНОЕ НАЗНАЧЕНИЕ:
    - Отображение основной статистики (пользователи, доходы, активность)
    - Мониторинг финансовых показателей за разные периоды
    - Отслеживание активности пользователей и тренеров
    
    КЛЮЧЕВЫЕ МЕТРИКИ:
    - Общее количество пользователей, менеджеров, тренеров
    - Финансовая статистика (общий доход, месячный доход, рост)
    - Активные абонементы и предстоящие тренировки
    - Статистика за 30 дней и популярные услуги
    """
    
    # SUMMARY: Установка временных периодов для анализа
    today = timezone.now().date()
    month_ago = today - timedelta(days=30)
    
    # SUMMARY: Базовая статистика пользователей
    total_users = User.objects.filter(is_active=True).count()
    
    # SUMMARY: Статистика сотрудников по ролям
    active_managers = User.objects.filter(
        groups__name='Менеджер по продажам',
        is_active=True
    ).count()
    
    active_trainers = User.objects.filter(
        groups__name='Тренер',
        is_active=True
    ).count()
    
    # SUMMARY: Финансовая статистика с обработкой Decimal значений
    total_revenue_result = Payments.objects.aggregate(total=Sum('price'))
    total_revenue = total_revenue_result['total'] or 0
    
    # Преобразуем в целое число если это Decimal
    if hasattr(total_revenue, 'to_integral_value'):
        total_revenue = int(total_revenue.to_integral_value())
    elif isinstance(total_revenue, float):
        total_revenue = int(total_revenue)
    
    monthly_revenue_result = Payments.objects.filter(
        paymentdate__gte=month_ago
    ).aggregate(total=Sum('price'))
    monthly_revenue = monthly_revenue_result['total'] or 0
    
    if hasattr(monthly_revenue, 'to_integral_value'):
        monthly_revenue = int(monthly_revenue.to_integral_value())
    elif isinstance(monthly_revenue, float):
        monthly_revenue = int(monthly_revenue)
    
    # SUMMARY: Расчет роста доходов за месяц
    previous_month = month_ago - timedelta(days=30)
    previous_revenue_result = Payments.objects.filter(
        paymentdate__gte=previous_month,
        paymentdate__lt=month_ago
    ).aggregate(total=Sum('price'))
    previous_revenue = previous_revenue_result['total'] or 0
    
    if hasattr(previous_revenue, 'to_integral_value'):
        previous_revenue = int(previous_revenue.to_integral_value())
    elif isinstance(previous_revenue, float):
        previous_revenue = int(previous_revenue)
    
    monthly_growth = 0
    if previous_revenue > 0:
        monthly_growth = round(((monthly_revenue - previous_revenue) / previous_revenue) * 100, 1)
    else:
        monthly_growth = 100 if monthly_revenue > 0 else 0
    
    # SUMMARY: Получение последних активностей для ленты событий
    recent_payments = Payments.objects.select_related(
        'subscription__subscriptiontype',
        'classclient__class_id'
    ).order_by('-paymentdate')[:5]
    
    recent_activities = []
    for payment in recent_payments:
        if payment.subscription:
            activity_type = 'subscription'
            title = f"Новый абонемент"
            user = payment.subscription.user
            try:
                user_profile = UserProfiles.objects.get(user=user)
                user_name = user_profile.full_name or user.username
            except UserProfiles.DoesNotExist:
                user_name = user.username
            description = payment.subscription.subscriptiontype.name
        else:
            activity_type = 'class'
            title = f"Запись на тренировку"
            user = payment.classclient.user
            try:
                user_profile = UserProfiles.objects.get(user=user)
                user_name = user_profile.full_name or user.username
            except UserProfiles.DoesNotExist:
                user_name = user.username
            description = payment.classclient.class_id.name
        
        recent_activities.append({
            'type': activity_type,
            'title': title,
            'user': user_name,
            'description': description,
            'time': payment.paymentdate,
            'amount': payment.price
        })
    
    # SUMMARY: Дополнительная статистика за 30-дневный период
    new_users_30d = User.objects.filter(
        date_joined__gte=month_ago,
        is_active=True
    ).count()
    
    total_payments_30d = Payments.objects.filter(
        paymentdate__gte=month_ago
    ).count()
    
    # Активные абонементы
    active_subscriptions = Subscriptions.objects.filter(
        is_active=True
    ).count()
    
    # Предстоящие тренировки
    upcoming_classes = Classes.objects.filter(
        starttime__gte=timezone.now(),
        is_active=True
    ).count()
    
    # Средний чек
    avg_receipt = 0
    if total_payments_30d > 0:
        avg_receipt = round(monthly_revenue / total_payments_30d, 2)
    
    # SUMMARY: Получение статистики базы данных
    db_stats = get_database_stats(request)
    
    # SUMMARY: Анализ популярных типов абонементов
    popular_subscriptions = []
    subscription_types = SubscriptionTypes.objects.all()
    for sub_type in subscription_types:
        sales_count = Subscriptions.objects.filter(
            subscriptiontype=sub_type,
            is_active=True
        ).count()
        
        total_revenue = Payments.objects.filter(
            subscription__subscriptiontype=sub_type
        ).aggregate(total=Sum('price'))['total'] or 0
        
        if sales_count > 0:
            popular_subscriptions.append({
                'name': sub_type.name,
                'price': sub_type.price,
                'sales_count': sales_count,
                'total_revenue': total_revenue
            })
    
    # Сортируем по количеству продаж
    popular_subscriptions = sorted(popular_subscriptions, key=lambda x: x['sales_count'], reverse=True)[:3]
    
    # SUMMARY: Дополнительные метрики для мониторинга
    payments_today = Payments.objects.filter(paymentdate__date=today).count()
    system_errors = 0  # Заглушка для будущей реализации
    
    context = {
        # Основная статистика
        'total_users': total_users,
        'active_managers': active_managers,
        'active_trainers': active_trainers,
        'total_revenue': total_revenue,
        'monthly_growth': monthly_growth,
        'active_subscriptions': active_subscriptions,
        'upcoming_classes': upcoming_classes,
        
        # Активности
        'recent_activities': recent_activities,
        
        # Расширенная статистика
        'new_users_30d': new_users_30d,
        'total_payments_30d': total_payments_30d,
        'avg_receipt': avg_receipt,
        'system_errors': system_errors,
        
        # Статистика БД
        'db_size': db_stats['db_size'],
        'table_count': db_stats['table_count'],
        'db_status': db_stats['db_status'],
        'db_status_text': db_stats['db_status_text'],
        
        # Дополнительные данные
        'payments_today': payments_today,
        'popular_subscriptions': popular_subscriptions,
    }
    
    return render(request, 'admin-home.html', context)

@admin_required
@login_required
def action_logs(request):
    """
    SUMMARY: Страница просмотра и фильтрации логов действий пользователей
    
    ОСНОВНОЕ НАЗНАЧЕНИЕ:
    - Отображение журнала действий пользователей с фильтрацией
    - Статистика действий по типам с визуализацией
    - Поиск и сортировка записей логов
    
    ФИЛЬТРЫ:
    - По периоду времени (7, 30, 90 дней, год, все время)
    - По роли пользователя
    - По конкретному пользователю
    - По типу действия
    - Поиск по тексту действия
    
    ВИЗУАЛИЗАЦИЯ:
    - Круговая диаграмма распределения действий по типам
    - Статистика по частоте действий
    """
    logs = UserActionsLog.objects.all()
    
    # SUMMARY: Фильтрация по периоду для диаграммы
    chart_period = request.GET.get('chart_period', '30')
    try:
        if chart_period != 'all':
            days = int(chart_period)
            since_date = timezone.now() - timedelta(days=days)
            logs = logs.filter(actiondate__gte=since_date)
    except ValueError:
        pass
    
    # SUMMARY: Фильтрация по различным параметрам
    role_filter = request.GET.get('role')
    if role_filter:
        logs = logs.filter(user__groups__name=role_filter)
    
    user_filter = request.GET.get('user')
    if user_filter:
        logs = logs.filter(user_id=user_filter)
    
    action_type_filter = request.GET.get('action_type')
    if action_type_filter:
        logs = logs.filter(action_type=action_type_filter)
    
    search_query = request.GET.get('search')
    if search_query:
        logs = logs.filter(action__icontains=search_query)
    
    # SUMMARY: Сортировка результатов
    sort_by = request.GET.get('sort', '-actiondate')
    if sort_by in ['actiondate', '-actiondate', 'user_full_name', '-user_full_name', 'action_type', '-action_type']:
        logs = logs.order_by(sort_by)
    
    # SUMMARY: Пагинация для удобства просмотра
    paginator = Paginator(logs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # SUMMARY: Получение данных для фильтров
    users = User.objects.filter(is_active=True).select_related('userprofile')
    roles = Group.objects.all()
    
    # SUMMARY: Подготовка данных для круговой диаграммы
    chart_logs = UserActionsLog.objects.all()
    if chart_period != 'all':
        try:
            days = int(chart_period)
            since_date = timezone.now() - timedelta(days=days)
            chart_logs = chart_logs.filter(actiondate__gte=since_date)
        except ValueError:
            pass
    
    # Получаем статистику по типам действий
    action_stats = chart_logs.values('action_type').annotate(
        count=models.Count('id')
    ).order_by('-count')
    
    # Преобразуем в удобный формат для JavaScript
    type_counts = {}
    total_chart_logs = 0
    for stat in action_stats:
        type_counts[stat['action_type'].lower()] = stat['count']
        total_chart_logs += stat['count']
    
    context = {
        'logs': page_obj,
        'users': users,
        'roles': roles,
        'action_types': UserActionsLog.ACTION_TYPES,
        'total_logs': paginator.count,
        'selected_period': chart_period,
        # Передаем статистику для диаграммы
        'chart_stats': {
            'total': total_chart_logs,
            'types': type_counts
        }
    }
    
    return render(request, 'action_logs.html', context)

# adminservice/views.py
@admin_required
@login_required
def backup_management(request):
    """
    SUMMARY: Страница управления резервным копированием базы данных
    """
    
    # SUMMARY: Используем относительный путь внутри проекта
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    backups = []
    
    print(f"BASE_DIR: {settings.BASE_DIR}")
    print(f"Проверяем папку: {backup_dir}")
    print(f"Папка существует: {os.path.exists(backup_dir)}")
    
    # Создаем папку если не существует
    os.makedirs(backup_dir, exist_ok=True)
    
    if os.path.exists(backup_dir):
        backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.sql') and f.startswith('fitzone_backup_')]
        print(f"Найдено файлов: {len(backup_files)}")
        
        # Сортируем по дате изменения (новые сначала)
        backup_files.sort(key=lambda x: os.path.getmtime(os.path.join(backup_dir, x)), reverse=True)
        backups = backup_files
    
    context = {
        'backups': backups,
        'backup_dir': backup_dir,
    }
    return render(request, 'backup_management.html', context)

@admin_required
@login_required
def create_backup(request):
    if request.method == 'POST':
        print("=== CREATE BACKUP STARTED ===")
        print(f"Request method: {request.method}")
        print(f"BASE_DIR: {settings.BASE_DIR}")
        
        try:
            backup_dir = os.path.join(settings.BASE_DIR, 'backups')
            print(f"Backup dir: {backup_dir}")
            
            # Проверим права на запись
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
                print(f"Created backup directory: {backup_dir}")
            
            # Проверим можем ли писать в папку
            test_file = os.path.join(backup_dir, 'test.txt')
            with open(test_file, 'w') as f:
                f.write('test')
            print(f"Test file created: {test_file}")
            
            # Создаем простой JSON бэкап через Django
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(backup_dir, f'fitzone_backup_{timestamp}.json')
            
            # Простой бэкап основных моделей
            from django.core import serializers
            from clientservice.models import UserProfiles, SubscriptionTypes, Classes
            
            data = {
                'user_profiles': serializers.serialize('json', UserProfiles.objects.all()[:10]),  # первые 10 для теста
                'timestamp': timestamp
            }
            
            with open(backup_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            file_size = os.path.getsize(backup_file)
            print(f"Backup created: {backup_file}, Size: {file_size} bytes")
            
            return JsonResponse({
                'success': True,
                'message': f'Бэкап создан: fitzone_backup_{timestamp}.json ({file_size} bytes)',
                'filename': f'fitzone_backup_{timestamp}.json'
            })
            
        except Exception as e:
            print(f"ERROR: {str(e)}")
            import traceback
            print(f"TRACEBACK: {traceback.format_exc()}")
            return JsonResponse({
                'success': False,
                'message': f'Ошибка: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Неверный метод запроса'})


@admin_required
@login_required
def restore_backup(request):
    """
    SUMMARY: Восстановление базы данных из резервной копии
    """
    if request.method == 'POST':
        backup_file = request.POST.get('backup_file')
        if not backup_file:
            return JsonResponse({'success': False, 'message': 'Файл бэкапа не указан'})
        
        try:
            # SUMMARY: Используем относительный путь внутри проекта
            backup_dir = os.path.join(settings.BASE_DIR, 'backups')
            backup_path = os.path.join(backup_dir, backup_file)
            
            if not os.path.exists(backup_path):
                return JsonResponse({'success': False, 'message': f'Файл бэкапа не найден: {backup_path}'})
            
            print(f"Восстанавливаем из: {backup_path}")
            
            psql_path = r'C:\Program Files\PostgreSQL\16\bin\psql.exe'
            
            
            # SUMMARY: Шаг 1 - Полная очистка базы данных
            print("Очищаем базу данных...")
            cleanup_cmd = [
                psql_path,
                '-h', settings.DATABASES['default']['HOST'],
                '-U', settings.DATABASES['default']['USER'],
                '-d', settings.DATABASES['default']['NAME'],
                '-c', "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
            ]
            
            env = os.environ.copy()
            env['PGPASSWORD'] = settings.DATABASES['default']['PASSWORD']
            
            # Очищаем базу
            cleanup_result = subprocess.run(
                cleanup_cmd, 
                env=env, 
                timeout=30,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            
            if cleanup_result.returncode != 0:
                return JsonResponse({
                    'success': False,
                    'message': f'Ошибка очистки базы: {cleanup_result.stderr[:500] if cleanup_result.stderr else "Неизвестная ошибка"}'
                })
            
            # SUMMARY: Шаг 2 - Восстановление данных из бэкапа
            print("Восстанавливаем данные...")
            restore_cmd = [
                psql_path,
                '-h', settings.DATABASES['default']['HOST'],
                '-U', settings.DATABASES['default']['USER'],
                '-d', settings.DATABASES['default']['NAME'],
                '-f', backup_path
            ]
            
            restore_result = subprocess.run(
                restore_cmd, 
                env=env, 
                timeout=60,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            
            print(f"Код возврата восстановления: {restore_result.returncode}")
            
            if restore_result.returncode == 0:
                return JsonResponse({
                    'success': True,
                    'message': f'✅ База данных полностью восстановлена из {backup_file}! Все новые данные удалены.'
                })
            else:
                error_msg = restore_result.stderr[:500] if restore_result.stderr else "Неизвестная ошибка"
                return JsonResponse({
                    'success': False,
                    'message': f'❌ Ошибка восстановления: {error_msg}'
                })
                
        except subprocess.TimeoutExpired:
            return JsonResponse({
                'success': False,
                'message': '⏰ Таймаут операции'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'❌ Ошибка: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Неверный метод запроса'})

@admin_required
@login_required
def export_payments(request):
    """
    SUMMARY: Экспорт данных о платежах в CSV формат
    
    ОСНОВНОЕ НАЗНАЧЕНИЕ:
    - Создание отчетов по финансовым операциям
    - Экспорт данных для внешнего анализа
    - Архивирование финансовой информации
    
    СТРУКТУРА ЭКСПОРТА:
    - ID платежа, тип, сумма, дата
    - Данные пользователя (ФИО, логин, email)
    - Детали платежа (абонемент/тренировка)
    """
    try:
        from clientservice.models import Payments, UserProfiles
        
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="payments_export.csv"'
        
        writer = csv.writer(response, delimiter=';', quoting=csv.QUOTE_ALL)
        
        writer.writerow([
            'ID платежа', 
            'Тип платежа', 
            'Сумма (руб)', 
            'Дата платежа', 
            'ФИО пользователя', 
            'Логин',
            'Email',
            'Детали платежа'
        ])
        
        # SUMMARY: Оптимизированный запрос с предзагрузкой связанных данных
        payments = Payments.objects.select_related(
            'subscription__user',
            'subscription__subscriptiontype',
            'classclient__user', 
            'classclient__class_id'
        ).order_by('-paymentdate')[:1000]
        
        # SUMMARY: Предзагрузка профилей пользователей для оптимизации
        user_ids = set()
        for payment in payments:
            if payment.subscription:
                user_ids.add(payment.subscription.user_id)
            else:
                user_ids.add(payment.classclient.user_id)
        
        profiles = UserProfiles.objects.filter(user_id__in=user_ids)
        profiles_dict = {profile.user_id: profile for profile in profiles}
        
        # SUMMARY: Формирование строк CSV
        for payment in payments:
            if payment.subscription:
                user = payment.subscription.user
                payment_type = 'Абонемент'
                details = payment.subscription.subscriptiontype.name if payment.subscription.subscriptiontype else 'Абонемент'
            else:
                user = payment.classclient.user
                payment_type = 'Тренировка'
                details = payment.classclient.class_id.name if payment.classclient.class_id else 'Тренировка'
            
            # Получаем ФИО из профиля
            profile = profiles_dict.get(user.id)
            full_name = ""
            
            if profile:
                if profile.full_name:
                    full_name = profile.full_name
                else:
                    name_parts = [profile.lastname, profile.firstname, profile.middlename]
                    full_name = ' '.join(part for part in name_parts if part).strip()
            
            # Если ФИО нет, используем логин
            if not full_name:
                full_name = user.username
            
            payment_date = payment.paymentdate.strftime('%d.%m.%Y %H:%M:%S')
            
            writer.writerow([
                payment.id,
                payment_type,
                str(payment.price).replace('.', ','),
                payment_date,
                full_name,
                user.username,
                user.email or "",
                details
            ])
        
        return response
        
    except Exception as e:
        print(f"Ошибка при экспорте: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Ошибка экспорта: {str(e)}'
        })

@admin_required
@login_required
def import_trainers(request):
    """
    SUMMARY: Импорт данных тренеров из CSV файла
    
    ОСНОВНОЕ НАЗНАЧЕНИЕ:
    - Массовое добавление тренеров в систему
    - Автоматическое создание учетных записей и профилей
    - Назначение специализаций тренерам
    
    ТРЕБОВАНИЯ К ФАЙЛУ:
    - Формат CSV с разделителем запятой или точки с запятой
    - Обязательные поля: email, password
    - Опциональные поля: first_name, last_name, specialization
    - Поддержка различных кодировок (UTF-8, Windows-1251)
    """
    if request.method == 'POST' and request.FILES.get('trainers_file'):
        try:
            from django.contrib.auth.models import User, Group
            from clientservice.models import UserProfiles, TrainerSpecializations
            
            file = request.FILES['trainers_file']
            print(f"Получен файл: {file.name}, размер: {file.size}")
            
            # SUMMARY: Проверка формата файла
            if not file.name.endswith('.csv'):
                return JsonResponse({
                    'success': False, 
                    'message': 'Файл должен быть в формате CSV, а не Excel'
                })
            
            # SUMMARY: Автоопределение кодировки файла
            encodings = ['utf-8', 'utf-8-sig', 'cp1251', 'windows-1251', 'iso-8859-1']
            decoded_content = None
            used_encoding = None
            
            for encoding in encodings:
                try:
                    file.seek(0)  # Сбрасываем позицию чтения файла
                    decoded_content = file.read().decode(encoding)
                    used_encoding = encoding
                    print(f"Успешно прочитано с кодировкой: {encoding}")
                    break
                except UnicodeDecodeError as e:
                    print(f"Не удалось прочитать с кодировкой {encoding}: {e}")
                    continue
            
            if decoded_content is None:
                return JsonResponse({
                    'success': False, 
                    'message': 'Не удалось прочитать файл. Попробуйте сохранить файл в кодировке UTF-8'
                })
            
            # Разделяем на строки
            decoded_file = decoded_content.splitlines()
            print(f"Количество строк: {len(decoded_file)}")
            
            # SUMMARY: Автоопределение разделителя
            possible_delimiters = [',', ';', '\t']
            reader = None
            used_delimiter = None
            
            for delimiter in possible_delimiters:
                try:
                    test_reader = csv.DictReader(decoded_file, delimiter=delimiter)
                    first_row = next(test_reader)
                    
                    # Проверяем, есть ли нужные поля
                    fieldnames_lower = [f.lower() for f in test_reader.fieldnames]
                    if 'email' in fieldnames_lower:
                        decoded_file = decoded_content.splitlines()
                        reader = csv.DictReader(decoded_file, delimiter=delimiter)
                        used_delimiter = delimiter
                        print(f"Успешно использован разделитель: '{delimiter}'")
                        print(f"Поля в CSV: {reader.fieldnames}")
                        break
                except Exception as e:
                    print(f"Разделитель '{delimiter}' не подошел: {e}")
                    continue
            
            if reader is None:
                # Пробуем стандартный читатель с правильной кодировкой
                try:
                    decoded_file = decoded_content.splitlines()
                    reader = csv.DictReader(decoded_file)
                    used_delimiter = ','
                    print(f"Поля в CSV (стандартный): {reader.fieldnames}")
                except Exception as e:
                    print(f"Стандартный читатель не сработал: {e}")
                    return JsonResponse({
                        'success': False,
                        'message': f'Не удалось прочитать CSV файл. Убедитесь, что файл в формате CSV с разделителем запятой или точки с запятой'
                    })
            
            # SUMMARY: Поиск обязательных полей в заголовках
            fieldnames_lower = [f.lower() for f in reader.fieldnames]
            print(f"Поля в нижнем регистре: {fieldnames_lower}")
            
            # Ищем email поле
            email_field = None
            for field in reader.fieldnames:
                if field.lower() in ['email', 'e-mail', 'почта', 'mail']:
                    email_field = field
                    break
            
            if not email_field:
                return JsonResponse({
                    'success': False,
                    'message': f'В файле отсутствует поле email. Найдены поля: {", ".join(reader.fieldnames)}'
                })
            
            # Ищем password поле
            password_field = None
            for field in reader.fieldnames:
                if field.lower() in ['password', 'пароль', 'pass']:
                    password_field = field
                    break
            
            if not password_field:
                return JsonResponse({
                    'success': False,
                    'message': f'В файле отсутствует поле password. Найдены поля: {", ".join(reader.fieldnames)}'
                })
            
            # SUMMARY: Обработка строк CSV
            imported_count = 0
            errors = []
            
            for row_num, row in enumerate(reader, 2):
                try:
                    # Используем найденные названия полей
                    email = row.get(email_field, '').strip()
                    password = row.get(password_field, '').strip()
                    first_name = row.get('first_name', row.get('firstname', row.get('имя', ''))).strip()
                    last_name = row.get('last_name', row.get('lastname', row.get('фамилия', ''))).strip()
                    specialization = row.get('specialization', row.get('специализация', '')).strip()
                    
                    print(f"Обрабатываем строку {row_num}: {email}")
                    
                    # Валидация
                    if not email:
                        errors.append(f'Строка {row_num}: Отсутствует email')
                        continue
                    
                    if not password:
                        errors.append(f'Строка {row_num}: Отсутствует пароль')
                        continue
                    
                    if User.objects.filter(email=email).exists():
                        errors.append(f'Строка {row_num}: Пользователь с email {email} уже существует')
                        continue
                    
                    # SUMMARY: Создание пользователя и профиля
                    username = email
                    user = User.objects.create(
                        username=username,
                        email=email,
                        first_name=first_name or '',
                        last_name=last_name or '',
                        is_active=True
                    )
                    user.set_password(password)
                    user.save()
                    
                    # Добавляем в группу тренеров
                    trainer_group, _ = Group.objects.get_or_create(name='Тренер')
                    user.groups.add(trainer_group)
                    
                    # Создаем профиль
                    UserProfiles.objects.create(
                        user=user,
                        firstname=first_name,
                        lastname=last_name
                    )
                    
                    # Добавляем специализацию
                    if specialization:
                        TrainerSpecializations.objects.create(
                            trainer=user,
                            specialization=specialization
                        )
                    
                    imported_count += 1
                    print(f"Успешно создан тренер: {email}")
                    
                except Exception as e:
                    error_msg = f'Строка {row_num}: {str(e)}'
                    errors.append(error_msg)
                    print(f"Ошибка: {error_msg}")
                    continue
            
            message = f'✅ Успешно импортировано {imported_count} тренеров'
            if errors:
                message += f'. Ошибки: {", ".join(errors[:3])}'
            
            return JsonResponse({
                'success': True,
                'message': message,
                'imported_count': imported_count,
                'error_count': len(errors)
            })
            
        except Exception as e:
            print(f"Общая ошибка импорта: {str(e)}")
            import traceback
            print(f"Трассировка: {traceback.format_exc()}")
            return JsonResponse({
                'success': False,
                'message': f'❌ Ошибка при импорте: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': '❌ Файл не загружен'})

@admin_required
@login_required
def staff_management(request):
    """
    SUMMARY: Страница управления сотрудниками (тренеры и менеджеры)
    
    ОСНОВНОЕ НАЗНАЧЕНИЕ:
    - Просмотр списка сотрудников с фильтрацией по активности
    - Создание, редактирование и деактивация сотрудников
    - Назначение ролей и специализаций
    
    ФИЛЬТРАЦИЯ:
    - Исключение администраторов и админов БД
    - Разделение на активных и неактивных сотрудников
    - Группировка по ролям (тренеры, менеджеры)
    """
    # Исключаем админов БД и администраторов
    excluded_groups = ['Админ БД', 'Администратор']
    
    # SUMMARY: Получение сотрудников с оптимизацией запросов
    staff_users = User.objects.filter(
        Q(groups__name='Тренер') | Q(groups__name='Менеджер по продажам')
    ).exclude(
        groups__name__in=excluded_groups
    ).distinct().select_related('userprofile').prefetch_related('groups').order_by('-is_active', 'first_name')
    
    # Получаем доступные группы для назначения
    available_groups = Group.objects.exclude(name__in=excluded_groups)
    
    # Статистика
    active_count = staff_users.filter(is_active=True).count()
    inactive_count = staff_users.filter(is_active=False).count()
    
    context = {
        'staff_users': staff_users,
        'available_groups': available_groups,
        'excluded_groups': excluded_groups,
        'active_count': active_count,
        'inactive_count': inactive_count,
        'total_count': staff_users.count(),
    }
    return render(request, 'staff_management.html', context)

@admin_required
@login_required
def delete_staff(request, user_id):
    """
    SUMMARY: Деактивация сотрудника (мягкое удаление)
    
    ОСНОВНОЕ НАЗНАЧЕНИЕ:
    - Установка флага is_active = False вместо физического удаления
    - Защита от деактивации администраторов
    - Сохранение исторических данных сотрудника
    
    ОГРАНИЧЕНИЯ:
    - Нельзя деактивировать пользователей с ролями 'Админ БД', 'Администратор'
    - Операция требует подтверждения
    """
    if request.method == 'POST':
        try:
            user = User.objects.get(id=user_id)
            
            # SUMMARY: Проверка прав доступа - защита администраторов
            excluded_groups = ['Админ БД', 'Администратор']
            if user.groups.filter(name__in=excluded_groups).exists():
                return JsonResponse({'success': False, 'message': 'Нельзя деактивировать администраторов'})
            
            # Деактивируем пользователя
            user.is_active = False
            user.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Сотрудник деактивирован'
            })
            
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Сотрудник не найден'})
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Ошибка при деактивации: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Неверный метод запроса'})

@admin_required
@login_required
def get_staff_data(request, user_id):
    """
    SUMMARY: Получение данных сотрудника для формы редактирования
    
    ОСНОВНОЕ НАЗНАЧЕНИЕ:
    - Предоставление данных для AJAX-запроса при редактировании
    - Извлечение данных из UserProfiles (ФИО) а не из стандартной модели User
    - Проверка прав доступа к редактированию
    
    ИСТОЧНИКИ ДАННЫХ:
    - Основные данные: модель User (email, активность)
    - Профильные данные: UserProfiles (ФИО)
    - Роль: группы пользователя
    """
    try:
        user = User.objects.get(id=user_id)
        
        # SUMMARY: Защита от редактирования администраторов
        excluded_groups = ['Админ БД', 'Администратор']
        if user.groups.filter(name__in=excluded_groups).exists():
            return JsonResponse({'success': False, 'message': 'Нельзя редактировать администраторов'})
        
        from clientservice.models import UserProfiles
        
        profile = user.userprofile
        group = user.groups.first()
        
        data = {
            'success': True,
            'user': {
                'id': user.id,
                'email': user.email,
                'firstname': profile.firstname if profile else '',  # Берем из UserProfiles
                'lastname': profile.lastname if profile else '',    # Берем из UserProfiles
                'middlename': profile.middlename if profile else '', # Берем из UserProfiles
                'group_id': group.id if group else None,
                'is_active': user.is_active
            }
        }
        
        return JsonResponse(data)
        
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Сотрудник не найден'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Ошибка: {str(e)}'})

@admin_required
@login_required
def create_staff(request):
    """
    SUMMARY: Создание нового сотрудника с полным профилем
    
    ОСНОВНОЕ НАЗНАЧЕНИЕ:
    - Создание учетной записи пользователя
    - Заполнение профиля UserProfiles (ФИО)
    - Назначение роли и специализации (для тренеров)
    - Автоматическая генерация логина из email
    
    ПРОЦЕСС СОЗДАНИЯ:
    1. Валидация обязательных полей (email, password)
    2. Создание пользователя с хешированием пароля
    3. Назначение группы (роли)
    4. Создание профиля с ФИО
    5. Добавление специализации для тренеров
    """
    if request.method == 'POST':
        try:
            email = request.POST.get('email')
            password = request.POST.get('password')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            middlename = request.POST.get('middlename', '')
            group_id = request.POST.get('group_id')
            specialization = request.POST.get('specialization', '')
            
            # SUMMARY: Базовая валидация обязательных полей
            if not email or not password:
                return JsonResponse({'success': False, 'message': 'Email и пароль обязательны'})
            
            if User.objects.filter(email=email).exists():
                return JsonResponse({'success': False, 'message': 'Пользователь с таким email уже существует'})
            
            # SUMMARY: Создание пользователя с безопасным хешированием пароля
            user = User.objects.create(
                username=email,
                email=email,
                is_active=True
            )
            user.set_password(password)
            user.save()
            
            # SUMMARY: Назначение роли и специализации
            if group_id:
                group = Group.objects.get(id=group_id)
                user.groups.add(group)
                
                # Если это тренер и указана специализация - создаем специализацию
                if group.name == 'Тренер' and specialization:
                    from clientservice.models import TrainerSpecializations
                    TrainerSpecializations.objects.create(
                        trainer=user,
                        specialization=specialization
                    )
            
            # SUMMARY: Создание расширенного профиля с ФИО
            from clientservice.models import UserProfiles
            UserProfiles.objects.create(
                user=user,
                firstname=first_name,
                lastname=last_name,
                middlename=middlename
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Сотрудник успешно создан'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Ошибка при создании сотрудника: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Неверный метод запроса'})

@admin_required
@login_required  
def update_staff(request, user_id):
    """
    SUMMARY: Обновление данных существующего сотрудника
    
    ОСНОВНОЕ НАЗНАЧЕНИЕ:
    - Обновление основных данных и статуса активности
    - Изменение роли пользователя
    - Обновление профиля UserProfiles (ФИО)
    - Управление специализацией тренеров
    
    ОСОБЕННОСТИ ОБНОВЛЕНИЯ:
    - При смене роли с "Тренер" на другую - удаляется специализация
    - Обновление ФИО происходит через модель UserProfiles
    - Защита от редактирования администраторов
    """
    if request.method == 'POST':
        try:
            user = User.objects.get(id=user_id)
            
            # SUMMARY: Защита от редактирования администраторов
            excluded_groups = ['Админ БД', 'Администратор']
            if user.groups.filter(name__in=excluded_groups).exists():
                return JsonResponse({'success': False, 'message': 'Нельзя редактировать администраторов'})
            
            first_name = request.POST.get('first_name', '')
            last_name = request.POST.get('last_name', '')
            middlename = request.POST.get('middlename', '')
            group_id = request.POST.get('group_id')
            is_active = request.POST.get('is_active') == 'true'
            specialization = request.POST.get('specialization', '')
            
            # SUMMARY: Обновление базовых данных пользователя
            user.is_active = is_active
            user.save()
            
            # SUMMARY: Обновление роли и связанных данных
            if group_id:
                user.groups.clear()
                group = Group.objects.get(id=group_id)
                user.groups.add(group)
                
                # SUMMARY: Управление специализацией тренера
                from clientservice.models import TrainerSpecializations
                if group.name == 'Тренер':
                    trainer_spec = TrainerSpecializations.objects.filter(trainer=user).first()
                    if specialization:
                        if trainer_spec:
                            trainer_spec.specialization = specialization
                            trainer_spec.save()
                        else:
                            TrainerSpecializations.objects.create(
                                trainer=user,
                                specialization=specialization
                            )
                    elif trainer_spec:
                        trainer_spec.delete()
                else:
                    # Удаляем специализацию если это не тренер
                    TrainerSpecializations.objects.filter(trainer=user).delete()
            
            # SUMMARY: Обновление профиля с ФИО
            from clientservice.models import UserProfiles
            profile, created = UserProfiles.objects.get_or_create(user=user)
            profile.firstname = first_name
            profile.lastname = last_name
            profile.middlename = middlename
            profile.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Данные сотрудника обновлены'
            })
            
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Сотрудник не найден'})
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Ошибка при обновлении: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Неверный метод запроса'})

@admin_required
@login_required
def get_trainer_specialization(request, user_id):
    """
    SUMMARY: Получение специализации тренера для AJAX-запросов
    
    ОСНОВНОЕ НАЗНАЧЕНИЕ:
    - Предоставление данных о специализации при редактировании тренера
    - Используется для динамического обновления интерфейса
    - Интеграция с формами редактирования сотрудников
    """
    try:
        from clientservice.models import TrainerSpecializations
        
        specialization = TrainerSpecializations.objects.filter(trainer_id=user_id).first()
        
        data = {
            'success': True,
            'specialization': specialization.specialization if specialization else ''
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Ошибка: {str(e)}'})