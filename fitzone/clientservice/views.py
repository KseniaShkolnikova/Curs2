from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from .forms import *
from .models import *
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
import json
from datetime import time  # Добавьте этот импорт
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta
from django.db import transaction



import random
from django.shortcuts import render

def home_view(request):
    print("=== DEBUG: Home view started ===")
    
    # Получаем популярные абонементы (первые 3)
    featured_subscriptions = SubscriptionTypes.objects.all().order_by('id')[:3]
    print(f"Found {featured_subscriptions.count()} subscriptions")
    
    # Получаем БУДУЩИЕ активные групповые занятия (исключаем персональные)
    featured_classes = Classes.objects.filter(
        is_active=True,
        starttime__gt=timezone.now()
    ).exclude(
        name__icontains='Персональная'  # Исключаем персональные тренировки
    ).select_related(
        'trainer', 
        'trainer__userprofile'
    ).order_by('starttime')[:6]  # Берем 6 ближайших
    
    print(f"Found {featured_classes.count()} group classes")
    for cls in featured_classes:
        print(f"Class: {cls.name}, Trainer: {cls.trainer.username}")
    
    # Получаем тренеров из группы "Тренер"
    featured_trainers = User.objects.filter(
        groups__name='Тренер',
        is_active=True
    ).select_related('userprofile')[:4]  # Берем 4 тренера
    
    print(f"Found {featured_trainers.count()} trainers")
    for trainer in featured_trainers:
        try:
            profile = trainer.userprofile
            print(f"Trainer: {trainer.username}, Full name: {profile.full_name}")
        except:
            print(f"Trainer: {trainer.username}, No profile")
    
    # Списки изображений для случаев когда нет своих фото
    class_images_list = [
        "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?ixlib=rb-4.0.3&auto=format&fit=crop&w=2070&q=80",
        "https://images.unsplash.com/photo-1534368420603-ba5d17c4e7b3?ixlib=rb-4.0.3&auto=format&fit=crop&w=2070&q=80",
        "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?ixlib=rb-4.0.3&auto=format&fit=crop&w=2070&q=80",
        "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?ixlib=rb-4.0.3&auto=format&fit=crop&w=2120&q=80",
        "https://images.unsplash.com/photo-1506126613408-eca07ce68773?ixlib=rb-4.0.3&auto=format&fit=crop&w=2022&q=80",
        "https://images.unsplash.com/photo-1599901860904-17e6ed7083a0?ixlib=rb-4.0.3&auto=format&fit=crop&w=2070&q=80",
    ]
    
    trainer_images_list = [
        "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?ixlib=rb-4.0.3&auto=format&fit=crop&w=2070&q=80",
        "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?ixlib=rb-4.0.3&auto=format&fit=crop&w=2070&q=80",
        "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?ixlib=rb-4.0.3&auto=format&fit=crop&w=2120&q=80",
        "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?ixlib=rb-4.0.3&auto=format&fit=crop&w=2070&q=80",
    ]
    
    context = {
        'featured_subscriptions': featured_subscriptions,
        'featured_classes': featured_classes,
        'featured_trainers': featured_trainers,
        'class_images_list': class_images_list,
        'trainer_images_list': trainer_images_list,
    }
    return render(request, 'home.html', context)


def classes_view(request):
    # Получаем только будущие активные тренировки, исключая персональные
    classes = Classes.objects.filter(
        is_active=True,
        starttime__gt=timezone.now()
    ).exclude(
        name__icontains='Персональная'  # Исключаем только персональные тренировки
    ).select_related(
        'trainer', 
        'trainer__userprofile'
    ).order_by('starttime')
    
    # Добавляем вычисляемое поле для длительности в минутах
    for class_item in classes:
        duration = class_item.endtime - class_item.starttime
        class_item.duration_minutes = duration.total_seconds() // 60
        
        # Получаем полное имя тренера из профиля
        try:
            profile = class_item.trainer.userprofile
            class_item.trainer_full_name = profile.full_name
        except UserProfiles.DoesNotExist:
            class_item.trainer_full_name = class_item.trainer.username
    
    print("=== DEBUG: Classes page ===")
    print(f"Found {classes.count()} active future group classes")
    
    # Для отладки выведем названия всех найденных тренировок
    for class_item in classes:
        print(f"Class: {class_item.name}")
    
    context = {
        'classes': classes
    }
    return render(request, 'classes.html', context)



@login_required
def class_booking(request, class_id):
    """Страница записи на конкретную тренировку"""
    class_item = get_object_or_404(Classes, id=class_id, is_active=True)
    
    # Получаем профиль тренера для отображения
    try:
        trainer_profile = UserProfiles.objects.get(user=class_item.trainer)
        trainer_name = trainer_profile.full_name
    except UserProfiles.DoesNotExist:
        trainer_name = class_item.trainer.username
    
    # ИСПРАВЛЕНИЕ: проверяем ЛЮБУЮ запись, а не только активные
    existing_booking = ClassClient.objects.filter(
        class_id=class_item, 
        user=request.user
        # Убрали is_active=True - проверяем все записи
    ).exists()
    
    # Считаем количество свободных мест (только активные записи)
    booked_clients = ClassClient.objects.filter(
        class_id=class_item, 
        is_active=True  # Для подсчета мест учитываем только активные
    ).count()
    available_spots = class_item.maxclient - booked_clients
    
    if request.method == 'POST':
        if existing_booking:
            messages.error(request, 'Вы уже записаны на эту тренировку!')
            return redirect('classes')
        
        if available_spots <= 0:
            messages.error(request, 'К сожалению, на эту тренировку нет свободных мест.')
            return redirect('classes')
        
        # Создаем запись о записи на тренировку
        try:
            with transaction.atomic():
                class_client = ClassClient.objects.create(
                    class_id=class_item,
                    user=request.user,
                    amount=1,
                    is_active=True
                )
                
                # Создаем платеж
                payment = Payments.objects.create(
                    classclient=class_client,
                    price=class_item.price,
                    paymentdate=timezone.now()
                )
                
                # Логируем действие
                UserActionsLog.objects.create(
                    user=request.user,
                    action=f'Запись на тренировку: {class_item.name}'
                )
                
                messages.success(request, f'Вы успешно записались на тренировку "{class_item.name}"!')
                return redirect('classes')
                
        except Exception as e:
            messages.error(request, f'Ошибка при записи: {str(e)}')
    
    # Остальной код без изменений...
    duration = class_item.endtime - class_item.starttime
    duration_minutes = int(duration.total_seconds() // 60)

    context = {
        'class_item': class_item,
        'trainer_name': trainer_name,
        'existing_booking': existing_booking,
        'available_spots': available_spots,
        'booked_count': booked_clients,
        'duration_minutes': duration_minutes,
    }
    
    return render(request, 'class_booking.html', context)


@login_required
@require_http_methods(["POST"])
def process_class_payment(request, class_id):
    """Обработка оплаты тренировки"""
    try:
        data = json.loads(request.body)
        class_item = get_object_or_404(Classes, id=class_id, is_active=True)
        
        # Проверяем, не записан ли пользователь уже
        existing_booking = ClassClient.objects.filter(
            class_id=class_item, 
            user=request.user, 
            is_active=True
        ).exists()
        
        if existing_booking:
            return JsonResponse({
                'success': False,
                'message': 'Вы уже записаны на эту тренировку!'
            })
        
        # Проверяем наличие свободных мест
        booked_clients = ClassClient.objects.filter(class_id=class_item, is_active=True).count()
        if booked_clients >= class_item.maxclient:
            return JsonResponse({
                'success': False,
                'message': 'К сожалению, на эту тренировку нет свободных мест.'
            })
        
        # Создаем запись в БД
        with transaction.atomic():
            class_client = ClassClient.objects.create(
                class_id=class_item,
                user=request.user,
                amount=1,
                is_active=True
            )
            
            # Создаем платеж
            payment = Payments.objects.create(
                classclient=class_client,
                price=class_item.price,
                paymentdate=timezone.now()
            )
            
            # Логируем действие
            UserActionsLog.objects.create(
                user=request.user,
                action=f'Запись на тренировку: {class_item.name}'
            )
        
        return JsonResponse({
            'success': True,
            'message': 'Запись на тренировку прошла успешно!',
            'order_number': f"#{payment.id:06d}"
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Ошибка при обработке платежа: {str(e)}'
        })

def subscription_view(request):
    # Получаем все абонементы из БД
    all_subscriptions = SubscriptionTypes.objects.all()
    
    # Если пользователь авторизован, фильтруем уже купленные абонементы
    if request.user.is_authenticated:
        # Получаем ID всех активных абонементов пользователя
        user_active_subscription_ids = Subscriptions.objects.filter(
            user=request.user,
            is_active=True
        ).values_list('subscriptiontype_id', flat=True)
        
        # Исключаем уже купленные активные абонементы
        subscriptions = all_subscriptions.exclude(id__in=user_active_subscription_ids)
        
        print("=== DEBUG: Filtered subscriptions ===")
        print(f"User has {len(user_active_subscription_ids)} active subscriptions")
        print(f"Showing {subscriptions.count()} available subscriptions")
    else:
        # Для неавторизованных пользователей показываем все абонементы
        subscriptions = all_subscriptions
    
    print("=== DEBUG: Getting subscriptions from DB ===")
    print(f"Found {subscriptions.count()} subscriptions to show")
    
    for sub in subscriptions:
        print(f"ID: {sub.id}, Name: '{sub.name}', Price: {sub.price}, Days: {sub.durationdays}")
    
    return render(request, 'subscription.html', {
        'subscriptions': subscriptions
    })




def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Создаем профиль пользователя с темой по умолчанию
            UserProfiles.objects.create(user=user, theme=False)
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно! Добро пожаловать в FITZONE.')
            return redirect('home')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = RegistrationForm()
    
    return render(request, 'Auth/registration.html', {'form': form})




def login_view(request):
    # Если пользователь уже авторизован, перенаправляем по роли
    if request.user.is_authenticated:
        return redirect_by_role(request.user)
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            print(f"=== DEBUG LOGIN ===")
            print(f"Username from form: {username}")
            print(f"Password length: {len(password)}")
            
            # Аутентифицируем пользователя
            user = authenticate(request, username=username, password=password)
            print(f"Authenticated user: {user}")
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {user.username}!')
                return redirect_by_role(user)
            else:
                print("=== DEBUG: Authentication failed ===")
                # Проверим, существует ли пользователь
                try:
                    user_by_email = User.objects.get(email=username)
                    print(f"User exists by email: {user_by_email}")
                    print(f"Real username: {user_by_email.username}")
                except User.DoesNotExist:
                    print("No user found with this email")
                    
                messages.error(request, 'Неверный email или пароль.')
        else:
            print(f"=== DEBUG: Form errors: {form.errors} ===")
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = LoginForm()
    
    return render(request, 'Auth/login.html', {'form': form})





def redirect_by_role(user):
    """Перенаправляет пользователя в зависимости от его роли"""
    if user.is_superuser:
        return redirect('/admin/')
    elif user.groups.filter(name='Тренер').exists():
        return redirect('/trainer/')
    elif user.groups.filter(name='Клиент').exists():
        return redirect('home')
    elif user.groups.filter(name='Администратор').exists():
        return redirect('adminservice:admin_dashboard')  # ИСПРАВЛЕНО название
    elif user.groups.filter(name='Менеджер по продажам').exists():
        return redirect('menegerservice:manager_home')
    else:
        return redirect('home')
    



def logout_user(request):
    logout(request)
    return redirect('login')

@login_required
def profile_view(request):
    try:
        profile = UserProfiles.objects.get(user=request.user)
    except UserProfiles.DoesNotExist:
        profile = UserProfiles.objects.create(user=request.user, theme=False)

    is_trainer = request.user.groups.filter(name='Тренер').exists()
    is_client = request.user.groups.filter(name='Клиент').exists()

    # Получаем только активные и неистекшие абонементы
    from datetime import timedelta
    from django.utils import timezone
    
    if not is_trainer:
        # Сначала помечаем истекшие абонементы как неактивные
        user_subscriptions_all = Subscriptions.objects.filter(user=request.user).select_related('subscriptiontype')
        
        # Автоматически помечаем истекшие абонементы как неактивные
        for subscription in user_subscriptions_all:
            end_date = subscription.startdate + timedelta(days=subscription.subscriptiontype.durationdays)
            if timezone.now().date() > end_date and subscription.is_active:
                subscription.is_active = False
                subscription.save()
        
        # Теперь получаем только активные абонементы
        user_subscriptions = user_subscriptions_all.filter(is_active=True)
        
    else:
        user_subscriptions = []
    
    # Получаем активные тренировки
    active_trainings = ClassClient.objects.filter(
        user=request.user,
        is_active=True,
        class_id__is_active=True,
        class_id__starttime__gt=timezone.now()
    ).select_related('class_id', 'class_id__trainer', 'class_id__trainer__userprofile') if not is_trainer else []
    
    # Считаем активные абонементы
    active_subscriptions_count = user_subscriptions.count() if not is_trainer else 0
    total_subscriptions_count = user_subscriptions.count() if not is_trainer else 0

    print("=== DEBUG PROFILE VIEW ===")
    print(f"User: {request.user} (ID: {request.user.id})")
    print(f"Showing subscriptions: {total_subscriptions_count}")
    print(f"Active trainings: {active_trainings.count() if not is_trainer else 0}")

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Профиль успешно обновлен!')
                
                if 'theme' in form.changed_data:
                    if profile.theme:
                        messages.info(request, 'Темная тема применена!')
                    else:
                        messages.info(request, 'Светлая тема применена!')
                    
                return redirect('profile')
            except Exception as e:
                messages.error(request, f'Ошибка при сохранении: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'profile.html', {
        'profile': profile,
        'form': form,
        'user_subscriptions': user_subscriptions,
        'active_trainings': active_trainings,
        'active_subscriptions_count': active_subscriptions_count,
        'total_subscriptions_count': total_subscriptions_count,
        'is_trainer': is_trainer,
        'is_client': is_client,
    })





def subscription_detail(request, subscription_id):
    subscription = get_object_or_404(SubscriptionTypes, id=subscription_id)
    
    context = {
        'subscription': subscription,
    }
    
    return render(request, 'detail_subscription.html', context)

@login_required
def subscription_payment(request, subscription_id):
    # Используй правильную модель - SubscriptionTypes вместо Subscriptions
    subscription = get_object_or_404(SubscriptionTypes, id=subscription_id)
    
    # Генерация случайного номера заказа для демонстрации
    import random
    random_order_number = random.randint(100000, 999999)
    
    context = {
        'subscription': subscription,
        'random_order_number': random_order_number,
    }
    
    return render(request, 'subscription_payment.html', context)

@login_required
def process_payment(request, subscription_id):
    if request.method == 'POST':
        try:
            print(f"=== DEBUG: Starting payment process ===")
            
            # Парсим JSON данные
            data = json.loads(request.body)
            print(f"Form data: {data}")
            
            # Сохраняем паспортные данные в сессии для документа
            request.session['passport_series'] = data.get('passport_series', '')
            request.session['passport_number'] = data.get('passport_number', '')
            request.session['passport_issued'] = data.get('passport_issued', '')
            request.session['issue_date'] = data.get('issue_date', '')
            request.session['division_code'] = data.get('division_code', '')
            
            # Получаем тип абонемента
            subscription_type = get_object_or_404(SubscriptionTypes, id=subscription_id)
            
            # Используем транзакцию для надежности
            with transaction.atomic():
                # 1. Создаем запись в Subscriptions
                start_date = timezone.now().date()
                
                subscription = Subscriptions.objects.create(
                    user=request.user,
                    subscriptiontype=subscription_type,
                    startdate=start_date,
                    is_active=True
                )
                
                # 2. Создаем запись в Payments
                payment = Payments.objects.create(
                    subscription=subscription,
                    price=subscription_type.price,
                    paymentdate=timezone.now()
                )
                
                # 3. Логируем действие
                UserActionsLog.objects.create(
                    user=request.user,
                    action=f'Оплата абонемента: {subscription_type.name}'
                )
                
                # 4. Генерируем PDF документ
                pdf_buffer = io.BytesIO()
                p = canvas.Canvas(pdf_buffer, pagesize=A4)
                width, height = A4
                
                # Настройки шрифтов
                try:
                    # Попробуем зарегистрировать шрифты
                    pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
                    pdfmetrics.registerFont(TTFont('Arial-Bold', 'arialbd.ttf'))
                    font_name = 'Arial'
                except:
                    font_name = 'Helvetica'
                
                # ШАПКА ДОКУМЕНТА
                p.setFont(font_name + '-Bold', 16)
                p.drawCentredString(width/2, height-50, "ДОГОВОР ОКАЗАНИЯ УСЛУГ И АКТ ПРИЕМА-ПЕРЕДАЧИ")
                p.setFont(font_name, 10)
                p.drawCentredString(width/2, height-70, f"№ {payment.id} от {datetime.now().strftime('%d.%m.%Y')}")
                
                # ИНФОРМАЦИЯ О КОМПАНИИ
                y_position = height - 120
                
                p.setFont(font_name + '-Bold', 12)
                p.drawString(50, y_position, "ИСПОЛНИТЕЛЬ:")
                p.setFont(font_name, 10)
                p.drawString(50, y_position-20, "ООО 'FITZONE'")
                p.drawString(50, y_position-35, "ИНН: 1234567890, КПП: 123456789, ОГРН: 1234567890123")
                p.drawString(50, y_position-50, "Юридический адрес: г. Москва, ул. Фитнесная, д. 1")
                p.drawString(50, y_position-65, "Расчетный счет: 40702810123456789012")
                p.drawString(50, y_position-80, "Банк: ПАО 'СБЕРБАНК', БИК: 044525225, к/с: 30101810400000000225")
                p.drawString(50, y_position-95, "Генеральный директор: Школьникова Ксения Васильевна")
                
                # ИНФОРМАЦИЯ О КЛИЕНТЕ
                p.setFont(font_name + '-Bold', 12)
                p.drawString(50, y_position-125, "ЗАКАЗЧИК:")
                p.setFont(font_name, 10)
                
                # Получаем данные пользователя
                try:
                    profile = request.user.userprofile
                    client_name = profile.full_name or f"{profile.lastname or ''} {profile.firstname or ''} {profile.middlename or ''}".strip()
                    if not client_name:
                        client_name = request.user.get_full_name() or request.user.username
                except:
                    client_name = request.user.get_full_name() or request.user.username
                    
                p.drawString(50, y_position-145, f"ФИО: {client_name}")
                
                # Паспортные данные из сессии (если есть)
                passport_series = request.session.get('passport_series', 'XXXX')
                passport_number = request.session.get('passport_number', 'XXXXXX')
                passport_issued = request.session.get('passport_issued', 'Отделом УФМС России')
                issue_date = request.session.get('issue_date', datetime.now().strftime('%d.%m.%Y'))
                division_code = request.session.get('division_code', '000-000')
                
                p.drawString(50, y_position-160, f"Паспорт: серия {passport_series} № {passport_number}")
                p.drawString(50, y_position-175, f"Выдан: {passport_issued}")
                p.drawString(50, y_position-190, f"Дата выдачи: {issue_date}")
                p.drawString(50, y_position-205, f"Код подразделения: {division_code}")
                
                # ПРЕДМЕТ ДОГОВОРА
                y_position -= 240
                p.setFont(font_name + '-Bold', 12)
                p.drawString(50, y_position, "1. ПРЕДМЕТ ДОГОВОРА")
                p.setFont(font_name, 10)
                
                contract_text = [
                    "1.1. Исполнитель обязуется оказать Заказчику услуги по предоставлению доступа",
                    "к фитнес-центру 'FITZONE', а Заказчик обязуется оплатить эти услуги.",
                    "",
                    f"1.2. Наименование услуги: Абонемент '{subscription_type.name}'",
                    f"1.3. Срок действия: {subscription_type.durationdays} дней",
                    f"1.4. Дата начала: {start_date.strftime('%d.%m.%Y')}",
                    f"1.5. Стоимость: {payment.price} рублей 00 копеек",
                    "",
                    "1.6. Услуги включают в себя:"
                ]
                
                for i, line in enumerate(contract_text):
                    p.drawString(60, y_position-20-(i*15), line)
                
                # УСЛУГИ АБОНЕМЕНТА
                services_y = y_position-20-(len(contract_text)*15)
                services = []
                if subscription_type.gym_access:
                    services.append("✓ Доступ в тренажерный зал")
                if subscription_type.pool_access:
                    services.append("✓ Доступ в бассейн")
                if subscription_type.spa_access:
                    services.append("✓ Доступ в СПА-зону")

                if subscription_type.locker_room:
                    services.append("✓ Раздевалка")
                if subscription_type.towel_service:
                    services.append("✓ Полотенце")

                if subscription_type.nutrition_consultation:
                    services.append("✓ Консультация по питанию")
                
                for i, service in enumerate(services):
                    p.drawString(70, services_y-20-(i*15), service)
                
                # АКТ ПРИЕМА-ПЕРЕДАЧИ
                act_y = services_y-20-(len(services)*15) - 40
                p.setFont(font_name + '-Bold', 12)
                p.drawString(50, act_y, "АКТ ПРИЕМА-ПЕРЕДАЧИ № 1")
                p.setFont(font_name, 10)
                
                act_text = [
                    f"к Договору оказания услуг № {payment.id} от {datetime.now().strftime('%d.%m.%Y')}",
                    "",
                    "Исполнитель передал, а Заказчик принял следующие услуги:",
                    f"- Абонемент '{subscription_type.name}'",
                    f"- Срок действия: {subscription_type.durationdays} дней",
                    f"- Стоимость: {payment.price} рублей 00 копеек",
                    "",
                    "Услуги переданы в полном объеме, качество услуг соответствует условиям Договора.",
                    "Претензий к количеству и качеству оказанных услуг Заказчик не имеет."
                ]
                
                for i, line in enumerate(act_text):
                    p.drawString(60, act_y-20-(i*15), line)
                
                # ПОДПИСИ
                signature_y = act_y-20-(len(act_text)*15) - 50
                p.line(100, signature_y, 300, signature_y)
                p.drawString(100, signature_y-15, "Исполнитель: ООО 'FITZONE'")
                p.drawString(100, signature_y-30, "Генеральный директор")
                p.drawString(100, signature_y-45, "_________________________ К.В. Школьникова")
                p.drawString(100, signature_y-60, "М.П.")
                
                p.line(350, signature_y, 550, signature_y)
                p.drawString(350, signature_y-15, "Заказчик:")
                p.drawString(350, signature_y-30, "_________________________")
                p.drawString(350, signature_y-45, client_name)
                
                p.showPage()
                p.save()
                
                pdf_content = pdf_buffer.getvalue()
                pdf_buffer.close()
                
                # 5. Отправляем email с PDF вложением
                try:
                    from email import encoders
                    from email.mime.base import MIMEBase
                    from email.mime.multipart import MIMEMultipart
                    from email.mime.text import MIMEText
                    import smtplib
                    
                    # Создаем сообщение
                    msg = MIMEMultipart()
                    msg['From'] = settings.DEFAULT_FROM_EMAIL
                    msg['To'] = request.user.email
                    msg['Subject'] = f'Договор на абонемент {subscription_type.name} - FITZONE'
                    
                    # Текст письма
                    body = f"""
                    Уважаемый(ая) {client_name}!
                    
                    Благодарим вас за приобретение абонемента "{subscription_type.name}" в фитнес-центре FITZONE.
                    
                    Детали вашего заказа:
                    - Абонемент: {subscription_type.name}
                    - Срок действия: {subscription_type.durationdays} дней
                    - Дата начала: {start_date.strftime('%d.%m.%Y')}
                    - Стоимость: {payment.price} рублей
                    - Номер заказа: #{payment.id:06d}
                    
                    В приложении вы найдете официальный договор и акт приема-передачи.
                    
                    Желаем вам продуктивных тренировок и достижения ваших фитнес-целей!
                    
                    С уважением,
                    Команда FITZONE
                    """
                    
                    msg.attach(MIMEText(body, 'plain', 'utf-8'))
                    
                    # Добавляем PDF вложение
                    pdf_attachment = MIMEBase('application', 'pdf')
                    pdf_attachment.set_payload(pdf_content)
                    encoders.encode_base64(pdf_attachment)
                    pdf_attachment.add_header(
                        'Content-Disposition',
                        f'attachment; filename="Договор_FITZONE_{payment.id}.pdf"'
                    )
                    msg.attach(pdf_attachment)
                    
                    # Отправляем email
                    with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
                        server.starttls()
                        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
                        server.send_message(msg)
                    
                    print(f"=== DEBUG: Email с договором отправлен на {request.user.email}")
                    
                except Exception as e:
                    print(f"=== DEBUG: Ошибка отправки email: {e}")
                    # Не прерываем процесс, если email не отправился
                
                return JsonResponse({
                    'success': True,
                    'message': 'Оплата прошла успешно! Договор отправлен на вашу почту.',
                    'order_number': f"#{payment.id:06d}",
                    'subscription_name': subscription_type.name,
                    'amount': float(subscription_type.price),
                    'payment_id': payment.id
                })
                
        except Exception as e:
            print(f"=== DEBUG: Error in payment process: {e} ===")
            return JsonResponse({
                'success': False,
                'message': f'Ошибка при обработке платежа: {str(e)}'
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'message': 'Неверный метод запроса'
    }, status=405)


from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
import io
from datetime import datetime

@login_required
def generate_payment_document(request, payment_id):
    """Генерация официального документа об оплате абонемента"""
    try:
        # Находим платеж
        payment = Payments.objects.get(
            id=payment_id, 
            subscription__user=request.user
        )
        subscription = payment.subscription
        user = request.user
        
        # Создаем PDF
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # Настройки
        try:
            # Попробуем зарегистрировать шрифты
            pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
            pdfmetrics.registerFont(TTFont('Arial-Bold', 'arialbd.ttf'))
            font_name = 'Arial'
        except:
            font_name = 'Helvetica'
        
        # ШАПКА ДОКУМЕНТА
        p.setFont(font_name + '-Bold', 16)
        p.drawCentredString(width/2, height-50, "ДОГОВОР ОКАЗАНИЯ УСЛУГ И АКТ ПРИЕМА-ПЕРЕДАЧИ")
        p.setFont(font_name, 10)
        p.drawCentredString(width/2, height-70, f"№ {payment.id} от {datetime.now().strftime('%d.%m.%Y')}")
        
        # ИНФОРМАЦИЯ О КОМПАНИИ
        y_position = height - 120
        
        p.setFont(font_name + '-Bold', 12)
        p.drawString(50, y_position, "ИСПОЛНИТЕЛЬ:")
        p.setFont(font_name, 10)
        p.drawString(50, y_position-20, "ООО 'FITZONE'")
        p.drawString(50, y_position-35, "ИНН: 1234567890, КПП: 123456789, ОГРН: 1234567890123")
        p.drawString(50, y_position-50, "Юридический адрес: г. Москва, ул. Фитнесная, д. 1")
        p.drawString(50, y_position-65, "Расчетный счет: 40702810123456789012")
        p.drawString(50, y_position-80, "Банк: ПАО 'СБЕРБАНК', БИК: 044525225, к/с: 30101810400000000225")
        p.drawString(50, y_position-95, "Генеральный директор: Школьникова Ксения Васильевна")
        
        # ИНФОРМАЦИЯ О КЛИЕНТЕ
        p.setFont(font_name + '-Bold', 12)
        p.drawString(50, y_position-125, "ЗАКАЗЧИК:")
        p.setFont(font_name, 10)
        
        # Получаем данные пользователя
        try:
            profile = user.userprofile
            client_name = profile.full_name or f"{profile.lastname or ''} {profile.firstname or ''} {profile.middlename or ''}".strip()
            if not client_name:
                client_name = user.get_full_name() or user.username
        except:
            client_name = user.get_full_name() or user.username
            
        p.drawString(50, y_position-145, f"ФИО: {client_name}")
        
        # Паспортные данные из сессии (если есть)
        passport_series = request.session.get('passport_series', 'XXXX')
        passport_number = request.session.get('passport_number', 'XXXXXX')
        passport_issued = request.session.get('passport_issued', 'Отделом УФМС России')
        issue_date = request.session.get('issue_date', datetime.now().strftime('%d.%m.%Y'))
        division_code = request.session.get('division_code', '000-000')
        
        p.drawString(50, y_position-160, f"Паспорт: серия {passport_series} № {passport_number}")
        p.drawString(50, y_position-175, f"Выдан: {passport_issued}")
        p.drawString(50, y_position-190, f"Дата выдачи: {issue_date}")
        p.drawString(50, y_position-205, f"Код подразделения: {division_code}")
        
        # ПРЕДМЕТ ДОГОВОРА
        y_position -= 240
        p.setFont(font_name + '-Bold', 12)
        p.drawString(50, y_position, "1. ПРЕДМЕТ ДОГОВОРА")
        p.setFont(font_name, 10)
        
        contract_text = [
            "1.1. Исполнитель обязуется оказать Заказчику услуги по предоставлению доступа",
            "к фитнес-центру 'FITZONE', а Заказчик обязуется оплатить эти услуги.",
            "",
            f"1.2. Наименование услуги: Абонемент '{subscription.subscriptiontype.name}'",
            f"1.3. Срок действия: {subscription.subscriptiontype.durationdays} дней",
            f"1.4. Дата начала: {subscription.startdate.strftime('%d.%m.%Y')}",
            f"1.5. Стоимость: {payment.price} рублей 00 копеек",
            "",
            "1.6. Услуги включают в себя:"
        ]
        
        for i, line in enumerate(contract_text):
            p.drawString(60, y_position-20-(i*15), line)
        
        # УСЛУГИ АБОНЕМЕНТА
        services_y = y_position-20-(len(contract_text)*15)
        services = []
        if subscription.subscriptiontype.gym_access:
            services.append("✓ Доступ в тренажерный зал")
        if subscription.subscriptiontype.pool_access:
            services.append("✓ Доступ в бассейн")
        if subscription.subscriptiontype.spa_access:
            services.append("✓ Доступ в СПА-зону")

        if subscription.subscriptiontype.locker_room:
            services.append("✓ Раздевалка")
        if subscription.subscriptiontype.towel_service:
            services.append("✓ Полотенце")

        if subscription.subscriptiontype.nutrition_consultation:
            services.append("✓ Консультация по питанию")
        
        for i, service in enumerate(services):
            p.drawString(70, services_y-20-(i*15), service)
        
        # АКТ ПРИЕМА-ПЕРЕДАЧИ
        act_y = services_y-20-(len(services)*15) - 40
        p.setFont(font_name + '-Bold', 12)
        p.drawString(50, act_y, "АКТ ПРИЕМА-ПЕРЕДАЧИ № 1")
        p.setFont(font_name, 10)
        
        act_text = [
            f"к Договору оказания услуг № {payment.id} от {datetime.now().strftime('%d.%m.%Y')}",
            "",
            "Исполнитель передал, а Заказчик принял следующие услуги:",
            f"- Абонемент '{subscription.subscriptiontype.name}'",
            f"- Срок действия: {subscription.subscriptiontype.durationdays} дней",
            f"- Стоимость: {payment.price} рублей 00 копеек",
            "",
            "Услуги переданы в полном объеме, качество услуг соответствует условиям Договора.",
            "Претензий к количеству и качеству оказанных услуг Заказчик не имеет."
        ]
        
        for i, line in enumerate(act_text):
            p.drawString(60, act_y-20-(i*15), line)
        
        # ПОДПИСИ
        signature_y = act_y-20-(len(act_text)*15) - 50
        p.line(100, signature_y, 300, signature_y)
        p.drawString(100, signature_y-15, "Исполнитель: ООО 'FITZONE'")
        p.drawString(100, signature_y-30, "Генеральный директор")
        p.drawString(100, signature_y-45, "_________________________ К.В. Школьникова")
        p.drawString(100, signature_y-60, "М.П.")
        
        p.line(350, signature_y, 550, signature_y)
        p.drawString(350, signature_y-15, "Заказчик:")
        p.drawString(350, signature_y-30, "_________________________")
        p.drawString(350, signature_y-45, client_name)
        
        p.showPage()
        p.save()
        
        pdf = buffer.getvalue()
        buffer.close()
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Договор_FITZONE_{payment.id}.pdf"'
        return response
        
    except Payments.DoesNotExist:
        return HttpResponse("Документ не найден", status=404)
    except Exception as e:
        return HttpResponse(f"Ошибка генерации документа: {str(e)}", status=500)

def personal_training(request):
    """Отображаем список тренеров из базы данных"""
    
    print("=== DEBUG personal_training ===")
    
    # Ищем тренеров через группу "Тренер"
    trainers = User.objects.filter(
        groups__name='Тренер',
        is_active=True
    ).distinct()
    
    print(f"Found {trainers.count()} trainers in 'Тренер' group")
    
    # Создаем список тренеров с информацией
    trainers_data = []
    for trainer in trainers:
        try:
            profile = UserProfiles.objects.get(user=trainer)
            full_name = profile.full_name
            print(f"✓ Trainer found: {full_name}")
        except UserProfiles.DoesNotExist:
            full_name = trainer.get_full_name() or trainer.username
            print(f"✗ Profile not found, using: {full_name}")
        
        # Получаем специализации тренера
        specializations = TrainerSpecializations.objects.filter(trainer=trainer)
        specialization_list = [spec.specialization for spec in specializations]
        print(f"  Specializations: {specialization_list}")
        
        trainers_data.append({
            'id': trainer.id,
            'full_name': full_name,
            'specializations': specialization_list,
            'bio': "Профессиональный тренер с индивидуальным подходом",
            'rating': 4.8,
        })
    
    print(f"Final trainers data: {len(trainers_data)} trainers")
    
    context = {
        'trainers': trainers_data,
    }
    
    return render(request, 'personal_training.html', context)



@login_required
def book_personal_training(request, trainer_id):
    """Страница для записи к тренеру"""
    trainer = get_object_or_404(User, id=trainer_id, is_active=True)
    
    try:
        trainer_profile = UserProfiles.objects.get(user=trainer)
        trainer_full_name = trainer_profile.full_name
    except UserProfiles.DoesNotExist:
        trainer_full_name = trainer.get_full_name() or trainer.username
    
    # Получаем специализации тренера
    specializations = TrainerSpecializations.objects.filter(trainer=trainer)
    specialization_list = [spec.specialization for spec in specializations]
    
    # Генерируем доступные временные слоты
    available_slots = generate_available_slots(trainer)
    
    # ДЕТАЛЬНАЯ ПРОВЕРКА ПАКЕТОВ
    print("=== DEBUG: Checking ALL packages for user ===")
    all_packages = ClassClient.objects.filter(user=request.user, class_id__name__contains="Пакет")
    print(f"Total packages found: {all_packages.count()}")
    
    for p in all_packages:
        print(f"  Package ID: {p.id}, Class ID: {p.class_id.id}, Trainer: {p.class_id.trainer.id}, Amount: {p.amount}, Active: {p.is_active}, Name: {p.class_id.name}")
    
    # Проверяем активные пакеты этого тренера
    active_packages = ClassClient.objects.filter(
        user=request.user,
        class_id__trainer=trainer,
        class_id__name__contains="Пакет",
        is_active=True,
        amount__gt=0
    )
    
    print(f"=== DEBUG: Active packages for trainer {trainer_full_name}: {active_packages.count()} ===")
    for p in active_packages:
        print(f"  Active Package ID: {p.id}, Amount: {p.amount}")
    
    has_active_package = active_packages.exists()
    
    # Получаем планы тренировок
    training_plans = TrainingPlans.objects.filter(
        trainer=trainer,
        client=request.user
    ).order_by('-is_active', '-id')
    
    context = {
        'trainer': trainer,
        'trainer_profile': trainer_profile,
        'trainer_full_name': trainer_full_name,
        'specializations': specialization_list,
        'available_slots': available_slots,
        'has_active_package': has_active_package,
        'active_package': active_packages.first() if has_active_package else None,
        'training_plans': training_plans,
    }
    
    return render(request, 'book_personal_training.html', context)



def generate_available_slots(trainer):
    """Генерирует доступные временные слоты для тренера"""
    slots = []
    now = timezone.now()
    
    # Рабочие часы тренера (9:00 - 21:00)
    work_hours = range(9, 21)
    
    for day in range(7):
        current_date = now.date() + timedelta(days=day)
        
        # Пропускаем выходные (можно настроить)
        if current_date.weekday() >= 5:  # Суббота и воскресенье
            continue
            
        for hour in work_hours:
            # ИСПРАВЛЕНИЕ: используем datetime.time вместо timezone.time
            slot_start = timezone.make_aware(datetime.combine(current_date, time(hour, 0)))
            slot_end = slot_start + timedelta(hours=1)
            
            # Проверяем, что время в будущем
            if slot_start <= now:
                continue
            
            # Проверяем, свободен ли тренер в это время
            is_available = not Classes.objects.filter(
                trainer=trainer,
                starttime__lt=slot_end,
                endtime__gt=slot_start,
                is_active=True
            ).exists()
            
            # ДОПОЛНИТЕЛЬНО: проверяем, нет ли уже персональных тренировок в это время
            # (если у вас есть модель для персональных тренировок)
            # is_available = is_available and not PersonalTraining.objects.filter(
            #     trainer=trainer,
            #     start_time__lt=slot_end,
            #     end_time__gt=slot_start,
            #     is_active=True
            # ).exists()
            
            if is_available:
                slots.append({
                    'datetime': slot_start,
                    'display': slot_start.strftime('%d.%m.%Y %H:%M')
                })
    
    # Сортируем слоты по дате
    slots.sort(key=lambda x: x['datetime'])
    
    return slots

@login_required
def create_personal_training(request, trainer_id):
    """Создание персональной тренировки"""
    print("=== DEBUG: create_personal_training called ===")
    
    if request.method == 'POST':
        try:
            trainer = get_object_or_404(User, id=trainer_id, is_active=True)
            start_time_str = request.POST.get('start_time')
            use_package = request.POST.get('use_package') == 'true'
            
            if not start_time_str:
                messages.error(request, 'Пожалуйста, выберите время тренировки.')
                return redirect('book_personal_training', trainer_id=trainer_id)
            
            # Преобразуем строку времени в datetime
            from django.utils.dateparse import parse_datetime
            start_time = parse_datetime(start_time_str)
            end_time = start_time + timedelta(hours=1)
            
            # Проверяем доступность тренера
            is_available = not Classes.objects.filter(
                trainer=trainer,
                starttime__lt=end_time,
                endtime__gt=start_time,
                is_active=True
            ).exists()
            
            if not is_available:
                messages.error(request, 'К сожалению, это время уже занято.')
                return redirect('book_personal_training', trainer_id=trainer_id)
            
            # Получаем имя тренера
            try:
                trainer_name = trainer.userprofile.full_name
            except:
                trainer_name = trainer.username
            
            # Создаем тренировку в базе данных
            with transaction.atomic():
                if use_package:
                    # ИЩЕМ ПАКЕТЫ ЭТОГО ТРЕНЕРА
                    active_packages = ClassClient.objects.filter(
                        user=request.user,
                        class_id__trainer=trainer,
                        class_id__name__contains="Пакет",
                        is_active=True,
                        amount__gt=0
                    ).select_for_update()
                    
                    print(f"=== DEBUG: Found {active_packages.count()} active packages for trainer {trainer_name} ===")
                    
                    # Выводим детальную информацию о пакетах
                    for p in active_packages:
                        print(f"  Package ID: {p.id}, Class ID: {p.class_id.id}, Amount: {p.amount}, Name: {p.class_id.name}")
                    
                    if not active_packages.exists():
                        messages.error(request, 'У вас нет активных пакетов тренировок у этого тренера.')
                        return redirect('book_personal_training', trainer_id=trainer_id)
                    
                    active_package = active_packages.first()
                    print(f"=== DEBUG: Using package ID {active_package.id}, current amount: {active_package.amount} ===")
                    
                    # Уменьшаем количество тренировок в пакете
                    active_package.amount -= 1
                    active_package.save()
                    print(f"=== DEBUG: Package amount after decrement: {active_package.amount} ===")
                    
                    # Если пакет закончился, делаем его неактивным
                    if active_package.amount <= 0:
                        active_package.is_active = False
                        active_package.save()
                        print("=== DEBUG: Package deactivated (amount reached 0) ===")
                    
                    # Создаем тренировку
                    personal_class = Classes.objects.create(
                        trainer=trainer,
                        name=f"Персональная тренировка с {trainer_name}",
                        description="Индивидуальная тренировка с персональным тренером",
                        starttime=start_time,
                        endtime=end_time,
                        maxclient=1,
                        price=0,
                        is_active=True
                    )
                    print(f"=== DEBUG: Created class with package: {personal_class.id} ===")
                    
                    # Создаем запись о тренировке
                    class_client = ClassClient.objects.create(
                        class_id=personal_class,
                        user=request.user,
                        amount=1,
                        is_active=True
                    )
                    print(f"=== DEBUG: Created class_client for training: {class_client.id} ===")
                    
                else:
                    # Разовая тренировка с оплатой
                    personal_class = Classes.objects.create(
                        trainer=trainer,
                        name=f"Персональная тренировка с {trainer_name}",
                        description="Индивидуальная тренировка с персональным тренером",
                        starttime=start_time,
                        endtime=end_time,
                        maxclient=1,
                        price=1500,
                        is_active=True
                    )
                    print(f"=== DEBUG: Created class with payment: {personal_class.id} ===")
                    
                    class_client = ClassClient.objects.create(
                        class_id=personal_class,
                        user=request.user,
                        amount=1,
                        is_active=True
                    )
                    print(f"=== DEBUG: Created class_client: {class_client.id} ===")
                    
                    payment = Payments.objects.create(
                        classclient=class_client,
                        price=1500,
                        paymentdate=timezone.now()
                    )
                    print(f"=== DEBUG: Created payment: {payment.id} ===")
                
                # Логируем действие
                UserActionsLog.objects.create(
                    user=request.user,
                    action=f'Запись на персональную тренировку с тренером {trainer_name}'
                )
                print("=== DEBUG: Action logged ===")
                
                messages.success(request, 'Вы успешно записались на персональную тренировку!')
                print("=== DEBUG: Redirecting to profile ===")
                return redirect('profile')
                
        except Exception as e:
            print(f"=== DEBUG: Exception: {e} ===")
            import traceback
            print(f"=== DEBUG: Traceback: {traceback.format_exc()} ===")
            messages.error(request, f'Ошибка при записи: {str(e)}')
            return redirect('book_personal_training', trainer_id=trainer_id)
    
    print("=== DEBUG: Not POST method, redirecting ===")
    return redirect('personal_training')

@login_required
def cancel_training(request, class_id):
    """Отмена тренировки"""
    if request.method == 'POST':
        try:
            print(f"=== DEBUG: Canceling training {class_id} for user {request.user} ===")
            
            # Находим запись ClassClient
            class_client = get_object_or_404(
                ClassClient, 
                class_id=class_id, 
                user=request.user,
                is_active=True
            )
            
            print(f"=== DEBUG: Found ClassClient: {class_client.id}, Amount: {class_client.amount} ===")
            
            with transaction.atomic():
                # Проверяем, была ли это тренировка из пакета (цена = 0)
                is_from_package = class_client.class_id.price == 0
                print(f"=== DEBUG: Is from package: {is_from_package} ===")
                
                # Если это тренировка из пакета, возвращаем ее в пакет
                if is_from_package:
                    # Ищем активные пакеты пользователя (amount > 1)
                    active_packages = ClassClient.objects.filter(
                        user=request.user,
                        is_active=True,
                        amount__gt=1  # Только настоящие пакеты
                    )
                    
                    print(f"=== DEBUG: Found {active_packages.count()} active packages ===")
                    
                    if active_packages.exists():
                        active_package = active_packages.first()
                        active_package.amount += 1
                        active_package.save()
                        print(f"=== DEBUG: Returned training to package, new amount: {active_package.amount} ===")
                    else:
                        # Создаем новый пакет с 1 тренировкой
                        new_package = ClassClient.objects.create(
                            class_id=class_client.class_id,
                            user=request.user,
                            amount=1,
                            is_active=True
                        )
                        print(f"=== DEBUG: Created new package with amount: 1 ===")
                
                # Делаем запись неактивной
                class_client.is_active = False
                class_client.save()
                
                # Также делаем неактивной саму тренировку если это персональная
                class_item = class_client.class_id
                if "Персональная тренировка" in class_item.name:
                    class_item.is_active = False
                    class_item.save()
                    print(f"=== DEBUG: Personal training {class_item.id} deactivated ===")
                
                # Логируем действие
                UserActionsLog.objects.create(
                    user=request.user,
                    action=f'Отмена тренировки: {class_item.name}'
                )
                
                print(f"=== DEBUG: Training successfully canceled ===")
                messages.success(request, 'Тренировка успешно отменена!')
                
        except ClassClient.DoesNotExist:
            print(f"=== DEBUG: ClassClient not found ===")
            messages.error(request, 'Запись на тренировку не найдена.')
        except Exception as e:
            print(f"=== DEBUG: Error canceling training: {e} ===")
            messages.error(request, f'Ошибка при отмене тренировки: {str(e)}')
    
    return redirect('profile')

@login_required
@require_http_methods(["POST"])
def cancel_subscription(request, subscription_id):
    """Отмена абонемента (мягкое удаление)"""
    try:
        print(f"=== DEBUG: Canceling subscription {subscription_id} for user {request.user} ===")
        
        # Находим абонемент пользователя
        subscription = get_object_or_404(
            Subscriptions,
            id=subscription_id,
            user=request.user,
            is_active=True
        )
        
        print(f"=== DEBUG: Found subscription: {subscription.id}, Type: {subscription.subscriptiontype.name} ===")
        
        with transaction.atomic():
            # Вместо удаления делаем абонемент неактивным
            subscription.is_active = False
            subscription.save()
            
            # Логируем действие
            UserActionsLog.objects.create(
                user=request.user,
                action=f'Отмена абонемента: {subscription.subscriptiontype.name}'
            )
            
            print(f"=== DEBUG: Subscription successfully deactivated ===")
            messages.success(request, f'Абонемент "{subscription.subscriptiontype.name}" успешно отменен!')
            
    except Subscriptions.DoesNotExist:
        print(f"=== DEBUG: Subscription not found ===")
        messages.error(request, 'Абонемент не найден.')
    except Exception as e:
        print(f"=== DEBUG: Error canceling subscription: {e} ===")
        messages.error(request, f'Ошибка при отмене абонемента: {str(e)}')
    
    return redirect('profile')


@login_required
@require_http_methods(["POST"])
def buy_personal_package(request, trainer_id):
    """Покупка пакета персональных тренирок БЕЗ привязки ко времени"""
    try:
        print("=== DEBUG: buy_personal_package called ===")
        data = json.loads(request.body)
        amount = int(data.get('amount', 1))
        price_per_training = 1500
        total_price = price_per_training * amount
        
        print(f"Package data - amount: {amount}, total_price: {total_price}")
        
        trainer = get_object_or_404(User, id=trainer_id, is_active=True)
        
        # Получаем имя тренера
        try:
            trainer_name = trainer.userprofile.full_name
        except:
            trainer_name = trainer.username
        
        # Создаем запись в БД
        with transaction.atomic():
            # ПРОВЕРЯЕМ, есть ли уже активный пакет у пользователя у этого тренера
            existing_package = ClassClient.objects.filter(
                user=request.user,
                class_id__trainer=trainer,
                class_id__name__contains="Пакет",
                is_active=True
            ).first()

            if existing_package:
                print(f"=== DEBUG: Found existing package ID {existing_package.id}, current amount: {existing_package.amount} ===")
                
                # Увеличиваем количество тренировок в существующем пакете
                existing_package.amount += amount
                existing_package.save()
                
                # Обновляем цену класса
                existing_package.class_id.price = existing_package.amount * 1500
                existing_package.class_id.save()
                
                class_client = existing_package
                print(f"=== DEBUG: Updated package, new amount: {existing_package.amount} ===")
                
            else:
                print("=== DEBUG: No existing package found, creating new one ===")
                # Создаем фиктивную тренировку для пакета
                package_class = Classes.objects.create(
                    trainer=trainer,
                    name=f"Пакет персональных тренировок с {trainer_name}",
                    description=f"Пакет персональных тренировок с тренером {trainer_name}",
                    starttime=timezone.now(),
                    endtime=timezone.now() + timedelta(hours=1),
                    maxclient=1,
                    price=total_price,
                    is_active=True
                )
                print(f"=== DEBUG: Created package class: {package_class.id} ===")
                
                # Создаем запись в ClassClient для пакета
                class_client = ClassClient.objects.create(
                    class_id=package_class,
                    user=request.user,
                    amount=amount,
                    is_active=True
                )
                print(f"=== DEBUG: Created class_client package: {class_client.id} ===")
            
            # Создаем платеж
            payment = Payments.objects.create(
                classclient=class_client,
                price=total_price,
                paymentdate=timezone.now()
            )
            print(f"=== DEBUG: Created payment: {payment.id} ===")
            
            # Логируем действие
            UserActionsLog.objects.create(
                user=request.user,
                action=f'Покупка пакета из {amount} персональных тренировок'
            )
            print("=== DEBUG: Action logged ===")
        
        return JsonResponse({
            'success': True,
            'message': f'Пакет из {amount} тренировок успешно приобретен!',
            'amount': amount,
            'price': total_price
        })
        
    except Exception as e:
        print(f"=== DEBUG: Error in buy_personal_package: {e} ===")
        return JsonResponse({
            'success': False,
            'message': f'Ошибка при покупке пакета: {str(e)}'
        })

@login_required
@require_http_methods(["POST"])
def delete_account(request):
    """Деактивация аккаунта пользователя"""
    try:
        user = request.user
        
        # Проверяем, что пользователь не суперпользователь
        if user.is_superuser:
            return JsonResponse({
                'success': False,
                'message': 'Нельзя деактивировать аккаунт администратора.'
            })
        
        # Проверяем, что пользователь не в группе администраторов
        if user.groups.filter(name='Администратор').exists():
            return JsonResponse({
                'success': False,
                'message': 'Нельзя деактивировать аккаунт администратора.'
            })
        
        with transaction.atomic():
            # 1. Деактивируем все активные абонементы пользователя
            active_subscriptions = Subscriptions.objects.filter(
                user=user,
                is_active=True
            )
            for subscription in active_subscriptions:
                subscription.is_active = False
                subscription.save()
            
            # 2. Отменяем все будущие тренировки
            future_trainings = ClassClient.objects.filter(
                user=user,
                is_active=True,
                class_id__starttime__gt=timezone.now()
            )
            for training in future_trainings:
                training.is_active = False
                training.save()
            
            # 3. Деактивируем пользователя
            user.is_active = False
            user.save()
            
            # 4. Логируем действие
            UserActionsLog.objects.create(
                user=user,
                action='Деактивация аккаунта пользователем',
                action_type='SYSTEM'
            )
        
        # Выходим из системы
        logout(request)
        
        return JsonResponse({
            'success': True,
            'message': 'Ваш аккаунт успешно деактивирован. Все данные сохранены.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Ошибка при деактивации аккаунта: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def deactivate_account(request):
    """Деактивация аккаунта пользователя с проверкой пароля"""
    try:
        data = json.loads(request.body)
        password = data.get('password')
        user = request.user
        
        # Проверяем пароль
        if not user.check_password(password):
            return JsonResponse({
                'success': False,
                'message': 'Неверный пароль',
                'error_type': 'password'
            })
        
        # Проверяем, что пользователь не суперпользователь
        if user.is_superuser:
            return JsonResponse({
                'success': False,
                'message': 'Нельзя деактивировать аккаунт администратора.'
            })
        
        # Проверяем, что пользователь не в группе администраторов
        if user.groups.filter(name='Администратор').exists():
            return JsonResponse({
                'success': False,
                'message': 'Нельзя деактивировать аккаунт администратора.'
            })
        
        with transaction.atomic():
            # 1. Деактивируем все активные абонементы пользователя
            active_subscriptions = Subscriptions.objects.filter(
                user=user,
                is_active=True
            )
            for subscription in active_subscriptions:
                subscription.is_active = False
                subscription.save()
            
            # 2. Отменяем все будущие тренировки
            future_trainings = ClassClient.objects.filter(
                user=user,
                is_active=True,
                class_id__starttime__gt=timezone.now()
            )
            for training in future_trainings:
                training.is_active = False
                training.save()
            
            # 3. Деактивируем пользователя (вместо удаления)
            user.is_active = False
            user.save()
            
            # 4. Логируем действие
            UserActionsLog.objects.create(
                user=user,
                action='Деактивация аккаунта пользователем',
                action_type='SYSTEM'
            )
        
        # Выходим из системы
        logout(request)
        
        return JsonResponse({
            'success': True,
            'message': 'Ваш аккаунт успешно деактивирован. Все данные сохранены. Для восстановления обратитесь в поддержку.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Ошибка при деактивации аккаунта: {str(e)}'
        })

@login_required
@require_http_methods(["POST"])
def process_personal_payment(request, trainer_id):
    """Обработка оплаты РАЗОВОЙ персональной тренировки"""
    try:
        print("=== DEBUG: process_personal_payment called ===")
        data = json.loads(request.body)
        print(f"Payment data: {data}")
        
        trainer = get_object_or_404(User, id=trainer_id, is_active=True)
        start_time_str = data.get('start_time')
        price = 1500  # Фиксированная цена для разовой тренировки
        
        if not start_time_str:
            return JsonResponse({
                'success': False,
                'message': 'Пожалуйста, выберите время тренировки.'
            })
        
        # Преобразуем строку времени в datetime
        from django.utils.dateparse import parse_datetime
        start_time = parse_datetime(start_time_str)
        end_time = start_time + timedelta(hours=1)
        
        # Проверяем доступность тренера
        is_available = not Classes.objects.filter(
            trainer=trainer,
            starttime__lt=end_time,
            endtime__gt=start_time,
            is_active=True
        ).exists()
        
        if not is_available:
            return JsonResponse({
                'success': False,
                'message': 'К сожалению, это время уже занято.'
            })
        
        # Получаем имя тренера
        try:
            trainer_name = trainer.userprofile.full_name
        except:
            trainer_name = trainer.username
        
        # Создаем тренировку в базе данных
        with transaction.atomic():
            print("=== DEBUG: Creating single training ===")
            
            # Создаем запись в Classes
            personal_class = Classes.objects.create(
                trainer=trainer,
                name=f"Персональная тренировка с {trainer_name}",
                description="Индивидуальная тренировка с персональным тренером",
                starttime=start_time,
                endtime=end_time,
                maxclient=1,
                price=price,
                is_active=True
            )
            print(f"=== DEBUG: Created class: {personal_class.id} ===")
            
            # Создаем запись в ClassClient
            class_client = ClassClient.objects.create(
                class_id=personal_class,
                user=request.user,
                amount=1,
                is_active=True
            )
            print(f"=== DEBUG: Created class_client: {class_client.id} ===")
            
            # Создаем платеж
            payment = Payments.objects.create(
                classclient=class_client,
                price=price,
                paymentdate=timezone.now()
            )
            print(f"=== DEBUG: Created payment: {payment.id} ===")
            
            # Логируем действие
            UserActionsLog.objects.create(
                user=request.user,
                action=f'Оплата персональной тренировки с тренером {trainer_name}'
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Тренировка успешно оплачена и записана!',
                'order_number': f"#{payment.id:06d}"
            })
        
    except Exception as e:
        print(f"=== DEBUG: Error in process_personal_payment: {e} ===")
        return JsonResponse({
            'success': False,
            'message': f'Ошибка при обработке платежа: {str(e)}'
        })



import random
import string
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.contrib.auth import update_session_auth_hash

def password_reset_view(request):
    """Восстановление и смена пароля с проверкой через email"""
    
    if request.method == 'POST':
        step = request.POST.get('step')
        
        if step == 'check_current':
            # Проверка текущего пароля - только для авторизованных
            if not request.user.is_authenticated:
                return JsonResponse({
                    'success': False,
                    'message': 'Для проверки текущего пароля необходимо войти в систему'
                })
            
            current_password = request.POST.get('current_password')
            
            if check_password(current_password, request.user.password):
                return JsonResponse({
                    'success': True,
                    'correct': True,
                    'step': 'check_current'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Неверный текущий пароль',
                    'step': 'check_current'
                })
        
        elif step == 'send_code':
            # Отправка кода на email - работает для всех
            email = request.POST.get('email')
            
            # Если пользователь авторизован, проверяем что email совпадает
            if request.user.is_authenticated and email != request.user.email:
                return JsonResponse({
                    'success': False,
                    'message': 'Указанный email не соответствует email вашего аккаунта'
                })
            
            # Для неавторизованных - проверяем что пользователь существует
            if not request.user.is_authenticated:
                try:
                    user = User.objects.get(email=email)
                except User.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'message': 'Пользователь с таким email не найден'
                    })
            
            # Генерируем 6-значный код
            code = ''.join(random.choices(string.digits, k=6))
            
            # Сохраняем код в сессии
            request.session['password_reset_code'] = code
            request.session['password_reset_email'] = email
            request.session['password_reset_attempts'] = 0
            # Сохраняем информацию о том, был ли пользователь авторизован изначально
            request.session['password_reset_was_authenticated'] = request.user.is_authenticated
            
            # Отправляем email
            try:
                send_mail(
                    'Код подтверждения для смены пароля - FITZONE',
                    f'Ваш код подтверждения: {code}\n\nКод действителен в течение 10 минут.',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                
                return JsonResponse({
                    'success': True,
                    'message': 'Код подтверждения отправлен на ваш email',
                    'step': 'send_code'
                })
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Ошибка при отправке email: {str(e)}'
                })
        
        elif step == 'verify_code':
            # Проверка кода подтверждения - работает для всех
            user_code = request.POST.get('verification_code')
            stored_code = request.session.get('password_reset_code')
            email = request.session.get('password_reset_email')
            attempts = request.session.get('password_reset_attempts', 0)
            
            if attempts >= 3:
                return JsonResponse({
                    'success': False,
                    'message': 'Превышено количество попыток. Запросите новый код.'
                })
            
            if not stored_code or not email:
                return JsonResponse({
                    'success': False,
                    'message': 'Сессия истекла. Запросите код заново.'
                })
            
            # Для авторизованных проверяем что email совпадает
            if request.user.is_authenticated and email != request.user.email:
                return JsonResponse({
                    'success': False,
                    'message': 'Ошибка сессии. Запросите код заново.'
                })
            
            if user_code == stored_code:
                # Код верный, очищаем сессию
                request.session.pop('password_reset_code', None)
                request.session.pop('password_reset_attempts', None)
                request.session['password_reset_verified'] = True
                
                return JsonResponse({
                    'success': True,
                    'message': 'Код подтвержден',
                    'step': 'verify_code'
                })
            else:
                # Увеличиваем счетчик попыток
                request.session['password_reset_attempts'] = attempts + 1
                remaining_attempts = 3 - (attempts + 1)
                
                return JsonResponse({
                    'success': False,
                    'message': f'Неверный код. Осталось попыток: {remaining_attempts}'
                })
        
        elif step == 'set_password':
            # Установка нового пароля - работает для всех
            new_password1 = request.POST.get('new_password1')
            new_password2 = request.POST.get('new_password2')
            email = request.session.get('password_reset_email')
            verified = request.session.get('password_reset_verified')
            was_authenticated = request.session.get('password_reset_was_authenticated', False)
            
            if not verified or not email:
                return JsonResponse({
                    'success': False,
                    'message': 'Сессия истекла. Начните процесс заново.'
                })
            
            if new_password1 != new_password2:
                return JsonResponse({
                    'success': False,
                    'message': 'Пароли не совпадают'
                })
            
            if len(new_password1) < 8:
                return JsonResponse({
                    'success': False,
                    'message': 'Пароль должен содержать минимум 8 символов'
                })
            
            # Находим пользователя
            try:
                if request.user.is_authenticated:
                    user = request.user
                else:
                    user = User.objects.get(email=email)
                
                # Меняем пароль
                user.set_password(new_password1)
                user.save()
                
                # Обновляем сессию если пользователь авторизован
                if request.user.is_authenticated:
                    update_session_auth_hash(request, user)
                
                # Очищаем сессию
                request.session.pop('password_reset_email', None)
                request.session.pop('password_reset_verified', None)
                request.session.pop('password_reset_was_authenticated', None)
                
                # Логируем действие
                UserActionsLog.objects.create(
                    user=user,
                    action='Смена пароля через систему восстановления'
                )
                
                # Определяем куда редиректить
                if was_authenticated:
                    # Если менял пароль из профиля - возвращаем в профиль
                    redirect_url = reverse('profile')
                else:
                    # Если восстанавливал пароль - авторизуем и на главную
                    user = authenticate(request, username=user.username, password=new_password1)
                    if user is not None:
                        login(request, user)
                    redirect_url = reverse('home')
                
                return JsonResponse({
                    'success': True,
                    'message': 'Пароль успешно изменен!',
                    'step': 'set_password',
                    'redirect_url': redirect_url
                })
                
            except User.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Пользователь не найден'
                })
    
    # GET запрос - показываем форму
    return render(request, 'Auth/password_reset.html')



from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
import io
from datetime import datetime

def generate_subscription_agreement(request, payment_id):
    """Генерация договора на абонемент"""
    try:
        payment = Payments.objects.get(id=payment_id, subscription__user=request.user)
        subscription = payment.subscription
        user = request.user
        
        # Создаем PDF
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # Настройки шрифтов
        try:
            pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
            font_name = 'Arial'
        except:
            font_name = 'Helvetica'
        
        # Заголовок документа
        p.setFont(font_name + '-Bold', 16)
        p.drawCentredString(width/2, height-50, "ДОГОВОР ОКАЗАНИЯ УСЛУГ")
        p.setFont(font_name, 10)
        p.drawCentredString(width/2, height-70, f"№ {payment.id} от {datetime.now().strftime('%d.%m.%Y')}")
        
        # Информация о сторонах
        y_position = height - 120
        
        p.setFont(font_name + '-Bold', 12)
        p.drawString(50, y_position, "ИСПОЛНИТЕЛЬ:")
        p.setFont(font_name, 10)
        p.drawString(50, y_position-20, "ООО 'FITZONE'")
        p.drawString(50, y_position-35, "ИНН: 1234567890, КПП: 123456789")
        p.drawString(50, y_position-50, "Юридический адрес: г. Москва, ул. Фитнесная, д. 1")
        p.drawString(50, y_position-65, "Генеральный директор: Школьникова Ксения Васильевна")
        p.drawString(50, y_position-80, "Тел.: +7 (495) 123-45-67")
        
        p.setFont(font_name + '-Bold', 12)
        p.drawString(50, y_position-120, "ЗАКАЗЧИК:")
        p.setFont(font_name, 10)
        
        # Получаем данные пользователя из профиля
        try:
            profile = user.userprofile
            client_name = profile.full_name or f"{profile.lastname or ''} {profile.firstname or ''} {profile.middlename or ''}".strip()
            if not client_name:
                client_name = user.get_full_name() or user.username
        except:
            client_name = user.get_full_name() or user.username
            
        p.drawString(50, y_position-140, f"ФИО: {client_name}")
        p.drawString(50, y_position-155, f"Паспорт: серия {request.session.get('passport_series', '0000')} номер {request.session.get('passport_number', '000000')}")
        p.drawString(50, y_position-170, f"Выдан: {request.session.get('passport_issued', '')}")
        p.drawString(50, y_position-185, f"Дата выдачи: {request.session.get('issue_date', '')}")
        p.drawString(50, y_position-200, f"Код подразделения: {request.session.get('division_code', '000-000')}")
        
        # Предмет договора
        y_position -= 240
        p.setFont(font_name + '-Bold', 12)
        p.drawString(50, y_position, "1. ПРЕДМЕТ ДОГОВОРА")
        p.setFont(font_name, 10)
        
        service_text = [
            "1.1. Исполнитель обязуется оказать Заказчику услуги по предоставлению доступа",
            "к фитнес-центру 'FITZONE', а Заказчик обязуется оплатить эти услуги.",
            "",
            f"1.2. Наименование абонемента: {subscription.subscriptiontype.name}",
            f"1.3. Срок действия: {subscription.subscriptiontype.durationdays} дней",
            f"1.4. Стоимость: {payment.price} рублей",
            "",
            "1.5. Услуги включают в себя:"
        ]
        
        for i, line in enumerate(service_text):
            p.drawString(60, y_position-20-(i*15), line)
        
        # Услуги абонемента
        services_y = y_position-20-(len(service_text)*15)
        services = []
        if subscription.subscriptiontype.gym_access:
            services.append("✓ Доступ в тренажерный зал")
        if subscription.subscriptiontype.pool_access:
            services.append("✓ Доступ в бассейн")
        if subscription.subscriptiontype.spa_access:
            services.append("✓ Доступ в СПА-зону")

        
        for i, service in enumerate(services):
            p.drawString(70, services_y-20-(i*15), service)
        
        # Права и обязанности
        rights_y = services_y-20-(len(services)*15) - 30
        p.setFont(font_name + '-Bold', 12)
        p.drawString(50, rights_y, "2. ПРАВА И ОБЯЗАННОСТИ СТОРОН")
        p.setFont(font_name, 10)
        
        rights_text = [
            "2.1. Заказчик обязан соблюдать правила посещения фитнес-центра.",
            "2.2. Исполнитель обязан обеспечить безопасность и качество услуг.",
            "2.3. Абонемент не подлежит возврату после активации.",
            "2.4. Заказчик может заморозить абонемент согласно условиям тарифа."
        ]
        
        for i, line in enumerate(rights_text):
            p.drawString(60, rights_y-20-(i*15), line)
        
        # Подписи
        signature_y = rights_y-20-(len(rights_text)*15) - 50
        p.line(100, signature_y, 300, signature_y)
        p.drawString(100, signature_y-15, "Исполнитель: ООО 'FITZONE'")
        p.drawString(100, signature_y-30, "Генеральный директор")
        p.drawString(100, signature_y-45, "_________________________ К.В. Школьникова")
        
        p.line(350, signature_y, 550, signature_y)
        p.drawString(350, signature_y-15, "Заказчик:")
        p.drawString(350, signature_y-30, "_________________________")
        p.drawString(350, signature_y-45, client_name)
        
        p.showPage()
        p.save()
        
        pdf = buffer.getvalue()
        buffer.close()
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Договор_абонемента_{payment.id}.pdf"'
        return response
        
    except Payments.DoesNotExist:
        return HttpResponse("Документ не найден", status=404)