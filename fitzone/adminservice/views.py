# adminservice/views.py
from django.contrib.auth.models import User, Group  # ДОБАВЬ Group
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from django.db import connection

# Правильные импорты
from django.contrib.auth.models import User
from clientservice.models import *

def get_database_stats():
    """Получение статистики базы данных"""
    stats = {}
    
    try:
        # Размер базы данных
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_size_pretty(pg_database_size('fitZone_DB'))")
            db_size = cursor.fetchone()[0]
            stats['db_size'] = db_size
    except:
        stats['db_size'] = "Недоступно"
    
    try:
        # Количество таблиц
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
        # Статус подключения
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        stats['db_status'] = 'status-ok'
        stats['db_status_text'] = 'Подключено'
    except:
        stats['db_status'] = 'status-error'
        stats['db_status_text'] = 'Ошибка'
    
    return stats


@login_required
def admin_dashboard(request):
    """Главная панель администратора клуба"""
    
    # Текущая дата и период
    today = timezone.now().date()
    month_ago = today - timedelta(days=30)
    
    # Основная статистика
    total_users = User.objects.filter(is_active=True).count()
    
    # Менеджеры
    active_managers = User.objects.filter(
        groups__name='Менеджер по продажам',
        is_active=True
    ).count()
    
    # Тренеры
    active_trainers = User.objects.filter(
        groups__name='Тренер',
        is_active=True
    ).count()
    
    # Финансовая статистика - ИСПРАВЛЕННЫЙ КОД
    total_revenue_result = Payments.objects.aggregate(
        total=Sum('price')
    )
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
    
    # Рост за месяц
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
    
    # Последние активности
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
    
    # Статистика за 30 дней
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
    
    # Статистика БД
    db_stats = get_database_stats()
    
    # Популярные абонементы (исправленный запрос)
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
    
    # Дополнительные данные для мониторинга
    payments_today = Payments.objects.filter(paymentdate__date=today).count()
    
    # Ошибки системы (заглушка)
    system_errors = 0
    
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




from django.core.paginator import Paginator

@login_required
def action_logs(request):
    """Страница логов действий пользователей"""
    logs = UserActionsLog.objects.all()
    
    # Фильтрация по периоду для диаграммы
    chart_period = request.GET.get('chart_period', '30')
    try:
        if chart_period != 'all':
            days = int(chart_period)
            since_date = timezone.now() - timedelta(days=days)
            logs = logs.filter(actiondate__gte=since_date)
    except ValueError:
        pass
    
    # Фильтрация по роли пользователя
    role_filter = request.GET.get('role')
    if role_filter:
        logs = logs.filter(user__groups__name=role_filter)
    
    # Фильтрация по конкретному пользователю
    user_filter = request.GET.get('user')
    if user_filter:
        logs = logs.filter(user_id=user_filter)
    
    # Фильтрация по типу действия
    action_type_filter = request.GET.get('action_type')
    if action_type_filter:
        logs = logs.filter(action_type=action_type_filter)
    
    # Поиск по названию действия
    search_query = request.GET.get('search')
    if search_query:
        logs = logs.filter(action__icontains=search_query)
    
    # Сортировка
    sort_by = request.GET.get('sort', '-actiondate')
    if sort_by in ['actiondate', '-actiondate', 'user_full_name', '-user_full_name', 'action_type', '-action_type']:
        logs = logs.order_by(sort_by)
    
    # Пагинация - 10 записей на страницу
    paginator = Paginator(logs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Получаем списки для фильтров
    users = User.objects.filter(is_active=True).select_related('userprofile')
    roles = Group.objects.all()
    
    # СТАТИСТИКА ДЛЯ ДИАГРАММЫ - получаем с сервера
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
import os
import json
import csv
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from django.db import connection
import subprocess
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

@login_required
def backup_management(request):
    """Страница управления бэкапами, импортом и экспортом"""
    
    # Получаем список существующих бэкапов из папки Загрузки
    downloads_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
    backup_dir = os.path.join(downloads_dir, 'fitzone_backups')
    backups = []
    
    print(f"Проверяем папку: {backup_dir}")  # Для отладки
    print(f"Папка существует: {os.path.exists(backup_dir)}")  # Для отладки
    
    if os.path.exists(backup_dir):
        backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.sql') and f.startswith('fitzone_backup_')]
        print(f"Найдено файлов: {len(backup_files)}")  # Для отладки
        for f in backup_files:
            file_path = os.path.join(backup_dir, f)
            file_size = os.path.getsize(file_path)
            print(f"Файл: {f}, Размер: {file_size} байт")  # Для отладки
        
        # Сортируем по дате изменения (новые сначала)
        backup_files.sort(key=lambda x: os.path.getmtime(os.path.join(backup_dir, x)), reverse=True)
        backups = backup_files  # Последние 10 бэкапов
    
    context = {
        'backups': backups,
        'backup_dir': backup_dir,
    }
    return render(request, 'backup_management.html', context)




@login_required
def create_backup(request):
    """Создание бэкапа базы данных"""
    if request.method == 'POST':
        try:
            # Сохраняем в папку Загрузки пользователя
            downloads_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
            backup_dir = os.path.join(downloads_dir, 'fitzone_backups')
            os.makedirs(backup_dir, exist_ok=True)
            
            print(f"Создаем папку для бэкапов: {backup_dir}")  # Для отладки
            
            # Генерируем имя файла с timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(backup_dir, f'fitzone_backup_{timestamp}.sql')
            
            print(f"Создаем бэкап: {backup_file}")  # Для отладки
            
            # Для Windows используем полный путь к pg_dump
            pg_dump_path = r'C:\Program Files\PostgreSQL\16\bin\pg_dump.exe'  # Измените путь если нужно
            
            # Команда для создания бэкапа PostgreSQL
            cmd = [
                pg_dump_path,
                '-h', settings.DATABASES['default']['HOST'],
                '-U', settings.DATABASES['default']['USER'],
                '-d', settings.DATABASES['default']['NAME'],
                '-f', backup_file
            ]
            
            print(f"Выполняем команду: {' '.join(cmd)}")  # Для отладки
            
            # Выполняем команду
            env = os.environ.copy()
            env['PGPASSWORD'] = settings.DATABASES['default']['PASSWORD']
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            print(f"Результат: код {result.returncode}")  # Для отладки
            if result.stdout:
                print(f"STDOUT: {result.stdout}")  # Для отладки
            if result.stderr:
                print(f"STDERR: {result.stderr}")  # Для отладки
            
            # Проверяем создался ли файл
            file_exists = os.path.exists(backup_file)
            file_size = os.path.getsize(backup_file) if file_exists else 0
            
            print(f"Файл создан: {file_exists}, Размер: {file_size} байт, Путь: {backup_file}")
            
            # Проверяем содержимое папки
            if os.path.exists(backup_dir):
                files_in_dir = os.listdir(backup_dir)
                print(f"Файлы в папке бэкапов: {files_in_dir}")  # Для отладки
            
            if result.returncode == 0 and file_exists:
                return JsonResponse({
                    'success': True,
                    'message': f'Бэкап успешно создан: fitzone_backup_{timestamp}.sql ({file_size} bytes)',
                    'filename': f'fitzone_backup_{timestamp}.sql',
                    'filepath': backup_file
                })
            else:
                error_msg = result.stderr if result.stderr else "Неизвестная ошибка"
                return JsonResponse({
                    'success': False,
                    'message': f'Ошибка при создании бэкапа: {error_msg}'
                })
                
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Исключение: {error_details}")  # Для отладки
            return JsonResponse({
                'success': False,
                'message': f'Ошибка: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Неверный метод запроса'})




@login_required
def restore_backup(request):
    """Восстановление базы данных из бэкапа с полной очисткой"""
    if request.method == 'POST':
        backup_file = request.POST.get('backup_file')
        if not backup_file:
            return JsonResponse({'success': False, 'message': 'Файл бэкапа не указан'})
        
        try:
            downloads_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
            backup_dir = os.path.join(downloads_dir, 'fitzone_backups')
            backup_path = os.path.join(backup_dir, backup_file)
            
            if not os.path.exists(backup_path):
                return JsonResponse({'success': False, 'message': f'Файл бэкапа не найден: {backup_path}'})
            
            print(f"Восстанавливаем из: {backup_path}")
            
            psql_path = r'C:\Program Files\PostgreSQL\16\bin\psql.exe'
            
            # Шаг 1: Очищаем базу данных (ОПАСНО!)
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
            
            # Шаг 2: Восстанавливаем из бэкапа
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






@login_required
def export_payments(request):
    """Экспорт платежей в CSV с улучшенной обработкой данных"""
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
        
        payments = Payments.objects.select_related(
            'subscription__user',
            'subscription__subscriptiontype',
            'classclient__user', 
            'classclient__class_id'
        ).order_by('-paymentdate')[:1000]
        
        # Предзагружаем профили пользователей для оптимизации
        user_ids = set()
        for payment in payments:
            if payment.subscription:
                user_ids.add(payment.subscription.user_id)
            else:
                user_ids.add(payment.classclient.user_id)
        
        # Получаем все профили одним запросом
        profiles = UserProfiles.objects.filter(user_id__in=user_ids)
        profiles_dict = {profile.user_id: profile for profile in profiles}
        
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
    

@login_required
def import_trainers(request):
    """Импорт тренеров из CSV"""
    if request.method == 'POST' and request.FILES.get('trainers_file'):
        try:
            from django.contrib.auth.models import User, Group
            from clientservice.models import UserProfiles, TrainerSpecializations
            
            file = request.FILES['trainers_file']
            print(f"Получен файл: {file.name}, размер: {file.size}")
            
            # Проверяем что это CSV, а не Excel
            if not file.name.endswith('.csv'):
                return JsonResponse({
                    'success': False, 
                    'message': 'Файл должен быть в формате CSV, а не Excel'
                })
            
            # Пробуем разные кодировки
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
            
            # Пробуем разные разделители с правильной кодировкой
            possible_delimiters = [',', ';', '\t']
            reader = None
            used_delimiter = None
            
            for delimiter in possible_delimiters:
                try:
                    # Используем уже декодированное содержимое
                    test_reader = csv.DictReader(decoded_file, delimiter=delimiter)
                    first_row = next(test_reader)
                    
                    # Проверяем, есть ли нужные поля
                    fieldnames_lower = [f.lower() for f in test_reader.fieldnames]
                    if 'email' in fieldnames_lower:
                        # Возвращаемся к началу
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
            
            # Проверяем наличие обязательных полей
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
                    
                    # Создаем пользователя
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


# adminservice/views.py
from django.contrib.auth.models import User, Group
from django.db.models import Q

@login_required
def staff_management(request):
    """Страница управления сотрудниками"""
    # Исключаем админов БД и администраторов
    excluded_groups = ['Админ БД', 'Администратор']
    
    # Получаем всех сотрудников (тренеров и менеджеров) - ВКЛЮЧАЯ НЕАКТИВНЫХ
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




@login_required
def create_staff(request):
    """Создание нового сотрудника"""
    if request.method == 'POST':
        try:
            email = request.POST.get('email')
            password = request.POST.get('password')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            group_id = request.POST.get('group_id')
            
            # Валидация
            if not email or not password:
                return JsonResponse({'success': False, 'message': 'Email и пароль обязательны'})
            
            if User.objects.filter(email=email).exists():
                return JsonResponse({'success': False, 'message': 'Пользователь с таким email уже существует'})
            
            # Создаем пользователя
            user = User.objects.create(
                username=email,
                email=email,
                first_name=first_name or '',
                last_name=last_name or '',
                is_active=True
            )
            user.set_password(password)
            user.save()
            
            # Добавляем в группу
            if group_id:
                group = Group.objects.get(id=group_id)
                user.groups.add(group)
            
            # Создаем профиль
            from clientservice.models import UserProfiles
            UserProfiles.objects.create(
                user=user,
                firstname=first_name,
                lastname=last_name
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

@login_required
def update_staff(request, user_id):
    """Обновление данных сотрудника"""
    if request.method == 'POST':
        try:
            user = User.objects.get(id=user_id, is_active=True)
            
            # Проверяем что это не админ
            excluded_groups = ['Админ БД', 'Администратор']
            if user.groups.filter(name__in=excluded_groups).exists():
                return JsonResponse({'success': False, 'message': 'Нельзя редактировать администраторов'})
            
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            group_id = request.POST.get('group_id')
            is_active = request.POST.get('is_active') == 'true'
            
            # Обновляем данные
            user.first_name = first_name or ''
            user.last_name = last_name or ''
            user.is_active = is_active
            user.save()
            
            # Обновляем группу
            if group_id:
                user.groups.clear()
                group = Group.objects.get(id=group_id)
                user.groups.add(group)
            
            # Обновляем профиль
            from clientservice.models import UserProfiles
            profile, created = UserProfiles.objects.get_or_create(user=user)
            profile.firstname = first_name
            profile.lastname = last_name
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


@login_required
def delete_staff(request, user_id):
    """Деактивация сотрудника"""
    if request.method == 'POST':
        try:
            user = User.objects.get(id=user_id)
            
            # Проверяем что это не админ
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


@login_required
def get_staff_data(request, user_id):
    """Получение данных сотрудника для редактирования"""
    try:
        user = User.objects.get(id=user_id, is_active=True)
        
        # Проверяем что это не админ
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
                'first_name': user.first_name,
                'last_name': user.last_name,
                'group_id': group.id if group else None,
                'is_active': user.is_active
            }
        }
        
        return JsonResponse(data)
        
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Сотрудник не найден'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Ошибка: {str(e)}'})

@login_required
def update_staff(request, user_id):
    """Обновление данных сотрудника"""
    if request.method == 'POST':
        try:
            user = User.objects.get(id=user_id)
            
            # Проверяем что это не админ
            excluded_groups = ['Админ БД', 'Администратор']
            if user.groups.filter(name__in=excluded_groups).exists():
                return JsonResponse({'success': False, 'message': 'Нельзя редактировать администраторов'})
            
            first_name = request.POST.get('first_name', '')
            last_name = request.POST.get('last_name', '')
            group_id = request.POST.get('group_id')
            is_active = request.POST.get('is_active') == 'true'
            
            print(f"Обновление пользователя {user_id}:")
            print(f"first_name: {first_name}")
            print(f"last_name: {last_name}")
            print(f"group_id: {group_id}")
            print(f"is_active: {is_active}")
            
            # Обновляем данные пользователя
            user.first_name = first_name
            user.last_name = last_name
            user.is_active = is_active
            user.save()
            
            # Обновляем группу
            if group_id:
                user.groups.clear()
                group = Group.objects.get(id=group_id)
                user.groups.add(group)
            
            # Обновляем профиль
            from clientservice.models import UserProfiles
            profile, created = UserProfiles.objects.get_or_create(user=user)
            profile.firstname = first_name
            profile.lastname = last_name
            profile.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Данные сотрудника обновлены'
            })
            
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Сотрудник не найден'})
        except Exception as e:
            print(f"Ошибка при обновлении: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Ошибка при обновлении: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Неверный метод запроса'})