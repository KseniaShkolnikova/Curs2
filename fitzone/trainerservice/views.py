import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.template.loader import render_to_string  # Добавьте эту строку
from datetime import datetime, timedelta
from clientservice.models import *
from django.views.decorators.http import require_http_methods

from .forms import TrainingPlanEditForm, TrainingPlanForm
@login_required
def get_class_data(request, class_id):
    """Получение данных занятия для редактирования"""
    try:
        class_item = get_object_or_404(Classes, id=class_id, trainer=request.user)
        
        data = {
            'id': class_item.id,
            'name': class_item.name,
            'description': class_item.description,
            'starttime': class_item.starttime.isoformat(),
            'endtime': class_item.endtime.isoformat(),
            'maxclient': class_item.maxclient,
            'price': class_item.price,
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def trainer_classes(request):
    """Страница занятий тренера"""
    # Получаем ВСЕ занятия тренера
    classes = Classes.objects.filter(
        trainer=request.user
    ).select_related('trainer').prefetch_related('classclient_set').order_by('-starttime')
    
    # Обрабатываем данные для шаблона
    classes_data = []
    now = timezone.now()
    
    for class_item in classes:
        # Получаем записанных клиентов
        clients = class_item.classclient_set.filter(is_active=True).select_related('user__userprofile')
        clients_data = []
        for client in clients:
            try:
                profile = client.user.userprofile
                clients_data.append({
                    'full_name': profile.full_name or client.user.username,
                    'phone': getattr(profile, 'phone', 'Не указан')
                })
            except UserProfiles.DoesNotExist:
                clients_data.append({
                    'full_name': client.user.username,
                    'phone': 'Не указан'
                })
        
        # Определяем статус
        if class_item.starttime <= now <= class_item.endtime:
            status = 'active'
            status_display = 'Идет сейчас'
        elif class_item.endtime < now:
            status = 'completed'
            status_display = 'Завершено'
        else:
            status = 'upcoming'
            status_display = 'Предстоящее'
        
        # Время до начала (только для предстоящих)
        time_until = ''
        if status == 'upcoming':
            delta = class_item.starttime - now
            if delta.days > 0:
                time_until = f"{delta.days} дн."
            else:
                hours = delta.seconds // 3600
                minutes = (delta.seconds % 3600) // 60
                if hours > 0:
                    time_until = f"{hours} ч. {minutes} мин."
                else:
                    time_until = f"{minutes} мин."
        
        # Время с момента завершения (для завершенных)
        time_since = ''
        if status == 'completed':
            delta = now - class_item.endtime
            if delta.days > 0:
                time_since = f"{delta.days} дн. назад"
            else:
                hours = delta.seconds // 3600
                if hours > 0:
                    time_since = f"{hours} ч. назад"
                else:
                    minutes = (delta.seconds % 3600) // 60
                    time_since = f"{minutes} мин. назад"
        
        # Проверяем, можно ли редактировать/отменять (не позже чем за 1 час до начала)
        # Только для предстоящих занятий
        if status == 'upcoming':
            time_until_start = class_item.starttime - now
            can_edit = time_until_start.total_seconds() >= 3600  # 1 час в секундах
        else:
            can_edit = False  # Для активных и завершенных редактирование невозможно
        
        classes_data.append({
            'id': class_item.id,
            'name': class_item.name,
            'description': class_item.description,
            'starttime': class_item.starttime,
            'endtime': class_item.endtime,
            'maxclient': class_item.maxclient,
            'price': class_item.price,
            'type': 'group' if class_item.maxclient > 1 else 'personal',
            'type_display': 'Групповое' if class_item.maxclient > 1 else 'Персональное',
            'current_clients': len(clients_data),
            'clients': clients_data,
            'status': status,
            'status_display': status_display,
            'time_until': time_until,
            'time_since': time_since,
            'is_upcoming': status == 'upcoming',
            'is_completed': status == 'completed',
            'is_active': status == 'active',
            'duration': (class_item.endtime - class_item.starttime).seconds // 60,
            'can_edit': can_edit  # Добавляем флаг возможности редактирования
        })
    
    # Статистика
    total_classes = len(classes_data)
    active_classes = len([c for c in classes_data if c['status'] == 'active'])
    upcoming_classes = len([c for c in classes_data if c['status'] == 'upcoming'])
    completed_classes = len([c for c in classes_data if c['status'] == 'completed'])
    
    context = {
        'classes': classes_data,
        'total_classes': total_classes,
        'active_classes': active_classes + upcoming_classes,  # Активные + предстоящие
        'upcoming_classes': upcoming_classes,
        'completed_classes': completed_classes,
        'total_clients': sum([len(c['clients']) for c in classes_data])
    }
    
    return render(request, 'trainer_clases.html', context)




@login_required
@require_http_methods(["POST"])
def create_class(request):
    """Создание нового занятия"""
    try:
        data = json.loads(request.body)
        
        # Валидация данных
        required_fields = ['name', 'starttime', 'endtime', 'maxclient', 'price']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({'success': False, 'message': f'Поле {field} обязательно'})
        
        # Преобразуем даты из ISO формата
        start_time_str = data['starttime']
        end_time_str = data['endtime']
        
        # Создаем aware datetime объекты напрямую из ISO строки
        start_time = timezone.datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        end_time = timezone.datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
        
        # Убедимся, что время сохраняется правильно
        print(f"Creating class with start: {start_time}, end: {end_time}")
        
        # Создание занятия
        class_item = Classes.objects.create(
            trainer=request.user,
            name=data['name'],
            description=data.get('description', ''),
            starttime=start_time,
            endtime=end_time,
            maxclient=data['maxclient'],
            price=data['price'],
            is_active=True
        )
        
        # Логируем действие
        UserActionsLog.objects.create(
            user=request.user,
            action=f'Создано занятие: {class_item.name}'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Занятие успешно создано',
            'class_id': class_item.id
        })
        
    except Exception as e:
        print(f"Error creating class: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Ошибка при создании занятия: {str(e)}'
        })
    

@login_required
@require_http_methods(["POST"])
def edit_class(request, class_id):
    """Редактирование занятия"""
    try:
        class_item = get_object_or_404(Classes, id=class_id, trainer=request.user)
        
        # Проверяем, можно ли редактировать (не позже чем за 1 час до начала)
        time_until_start = class_item.starttime - timezone.now()
        if time_until_start.total_seconds() < 3600:  # 1 час в секундах
            return JsonResponse({
                'success': False, 
                'message': 'Редактирование невозможно менее чем за 1 час до начала занятия'
            })
        
        data = json.loads(request.body)
        
        # Валидация данных
        required_fields = ['name', 'starttime', 'endtime', 'maxclient', 'price']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({'success': False, 'message': f'Поле {field} обязательно'})
        
        # Преобразуем даты из ISO формата
        start_time_str = data['starttime']
        end_time_str = data['endtime']
        
        # Создаем aware datetime объекты
        start_time = timezone.datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        end_time = timezone.datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
        
        # Обновление занятия
        class_item.name = data['name']
        class_item.description = data.get('description', '')
        class_item.starttime = start_time
        class_item.endtime = end_time
        class_item.maxclient = data['maxclient']
        class_item.price = data['price']
        class_item.save()
        
        # Логируем действие
        UserActionsLog.objects.create(
            user=request.user,
            action=f'Изменено занятие: {class_item.name}'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Занятие успешно обновлено'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Ошибка при обновлении занятия: {str(e)}'
        })

@login_required
@require_http_methods(["POST"])
def cancel_class(request, class_id):
    """Отмена занятия"""
    try:
        class_item = get_object_or_404(Classes, id=class_id, trainer=request.user)
        
        # Проверяем, можно ли отменить (не позже чем за 1 час до начала)
        time_until_start = class_item.starttime - timezone.now()
        if time_until_start.total_seconds() < 3600:  # 1 час в секундах
            return JsonResponse({
                'success': False, 
                'message': 'Отмена невозможна менее чем за 1 час до начала занятия'
            })
        
        class_name = class_item.name
        class_item.delete()
        
        # Логируем действие
        UserActionsLog.objects.create(
            user=request.user,
            action=f'Отменено занятие: {class_name}'
        )
        
        return JsonResponse({'success': True, 'message': 'Занятие отменено'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_http_methods(["POST"])
def delete_class(request, class_id):
    """Удаление занятия"""
    try:
        class_item = get_object_or_404(Classes, id=class_id, trainer=request.user)
        class_name = class_item.name
        class_item.delete()
        
        UserActionsLog.objects.create(
            user=request.user,
            action=f'Удалено занятие: {class_name}'
        )
        
        return JsonResponse({'success': True, 'message': 'Занятие удалено'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
def home(request):
    """Главная страница для тренеров"""
    # Проверяем, что пользователь действительно тренер
    if not request.user.groups.filter(name='Тренер').exists():
        from django.contrib import messages
        messages.error(request, 'Доступ только для тренеров')
        from django.shortcuts import redirect
        return redirect('clientservice:home')
    
    now = timezone.now()
    today = now.date()
    
    # Получаем сегодняшние тренировки тренера
    today_trainings = Classes.objects.filter(
        trainer=request.user,
        starttime__date=today,
        is_active=True
    ).order_by('starttime')
    
    # Обрабатываем данные для шаблона
    processed_today_trainings = []
    for training in today_trainings:
        # Определяем тип тренировки
        is_group = training.maxclient > 1
        
        # Определяем статус тренировки
        if training.starttime <= now <= training.endtime:
            status = 'ongoing'
            status_display = 'Идет сейчас'
        elif training.endtime < now:
            status = 'completed'
            status_display = 'Завершена'
        else:
            status = 'upcoming'
            status_display = 'Скоро'
        
        # Получаем имя клиента для персональных тренировок
        client_name = None
        if not is_group:
            # Для персональных тренировок получаем имя клиента
            try:
                class_client = ClassClient.objects.filter(
                    class_id=training,
                    is_active=True
                ).first()
                if class_client and class_client.user.userprofile:
                    client_name = class_client.user.userprofile.full_name
                elif class_client:
                    client_name = class_client.user.username
            except:
                client_name = "Клиент"
        
        processed_today_trainings.append({
            'id': training.id,
            'name': training.name,
            'starttime': training.starttime,
            'endtime': training.endtime,
            'maxclient': training.maxclient,
            'is_group': is_group,
            'current_clients': ClassClient.objects.filter(class_id=training, is_active=True).count(),
            'client_name': client_name,
            'is_upcoming': status == 'upcoming',
            'is_ongoing': status == 'ongoing',
            'is_completed': status == 'completed',
            'status_display': status_display,
        })
    
    # Ближайшие тренировки (будущие, начиная с завтра)
    upcoming_trainings = Classes.objects.filter(
        trainer=request.user,
        starttime__date__gt=today,
        is_active=True
    ).order_by('starttime')[:5]
    
    # Обрабатываем ближайшие тренировки
    processed_upcoming_trainings = []
    for training in upcoming_trainings:
        is_group = training.maxclient > 1
        
        processed_upcoming_trainings.append({
            'id': training.id,
            'name': training.name,
            'starttime': training.starttime,
            'endtime': training.endtime,
            'is_group': is_group,
        })
    
    # Статистика за неделю
    week_ago = today - timedelta(days=7)
    
    # Получаем все тренировки за неделю
    weekly_classes = Classes.objects.filter(
        trainer=request.user,
        starttime__date__gte=week_ago,
        is_active=True
    )
    
    # Считаем статистику
    weekly_stats = {
        'total_trainings': weekly_classes.count(),
        'group_classes': weekly_classes.filter(maxclient__gt=1).count(),
        'personal_trainings': weekly_classes.filter(maxclient=1).count(),
        'total_clients': ClassClient.objects.filter(
            class_id__trainer=request.user,
            class_id__starttime__date__gte=week_ago,
            is_active=True
        ).values('user').distinct().count(),
    }
    
    context = {
        'today': today,
        'today_trainings': processed_today_trainings,
        'upcoming_trainings': processed_upcoming_trainings,
        'weekly_stats': weekly_stats,
    }
    
    return render(request, 'trainer_home.html', context)







from django.db.models import Q, Count

@login_required
def my_clients(request):
    # Получаем текущего авторизованного тренера
    current_trainer = request.user
    
    # Находим всех пользователей, у которых когда-либо была тренировка с текущим тренером
    # через тренировочные планы ИЛИ групповые занятия
    
    # Пользователи из тренировочных планов
    training_plan_clients = User.objects.filter(
        client_plans__trainer=current_trainer
    ).distinct()
    
    # Пользователи из групповых занятий
    class_clients = User.objects.filter(
        classclient__class_id__trainer=current_trainer
    ).distinct()
    
    # Объединяем оба QuerySet
    all_clients = (training_plan_clients | class_clients).distinct()
    
    # Аннотируем количество тренировочных планов и групповых занятий для каждого клиента
    clients_with_stats = all_clients.annotate(
        training_plans_count=Count(
            'client_plans', 
            filter=Q(client_plans__trainer=current_trainer)
        ),
        classes_count=Count(
            'classclient', 
            filter=Q(classclient__class_id__trainer=current_trainer)
        )
    ).select_related('userprofile')
    
    context = {
        'clients': clients_with_stats
    }
    
    return render(request, 'my_clients.html', context)

@login_required
def client_details(request, client_id):
    client = get_object_or_404(User, id=client_id)
    current_trainer = request.user
    
    # Проверяем, что у клиента действительно были тренировки с этим тренером
    has_connection = TrainingPlans.objects.filter(
        trainer=current_trainer, 
        client=client
    ).exists() or ClassClient.objects.filter(
        user=client,
        class_id__trainer=current_trainer
    ).exists()
    
    if not has_connection:
        return redirect('my_clients')
    
    # Получаем тренировочные планы
    training_plans = TrainingPlans.objects.filter(
        trainer=current_trainer,
        client=client
    ).order_by('-is_active', '-id')
    
    # Получаем групповые занятия
    group_classes = ClassClient.objects.filter(
        user=client,
        class_id__trainer=current_trainer
    ).select_related('class_id').order_by('-class_id__starttime')
    
    # Получаем активные подписки
    active_subscriptions = Subscriptions.objects.filter(
        user=client,
        is_active=True
    ).select_related('subscriptiontype')
    
    # Статистика
    total_training_plans = training_plans.count()
    active_training_plans = training_plans.filter(is_active=True).count()
    total_classes = group_classes.count()
    
    # Дата регистрации и стаж
    registration_date = client.date_joined
    membership_duration = timezone.now() - registration_date
    membership_days = membership_duration.days
    membership_months = membership_days // 30
    membership_years = membership_days // 365
    
    context = {
        'client': client,
        'training_plans': training_plans,
        'group_classes': group_classes,
        'active_subscriptions': active_subscriptions,
        'total_training_plans': total_training_plans,
        'active_training_plans': active_training_plans,
        'total_classes': total_classes,
        'registration_date': registration_date,
        'membership_days': membership_days,
        'membership_months': membership_months,
        'membership_years': membership_years,
    }
    
    return render(request, 'client_details.html', context)


@login_required
def create_training_plan(request, client_id):
    client = get_object_or_404(User, id=client_id)
    current_trainer = request.user
    
    # Проверяем, что у клиента действительно были тренировки с этим тренером
    has_connection = TrainingPlans.objects.filter(
        trainer=current_trainer, 
        client=client
    ).exists() or ClassClient.objects.filter(
        user=client,
        class_id__trainer=current_trainer
    ).exists()
    
    if not has_connection:
        return redirect('trainerservice:my_clients')
    
    if request.method == 'POST':
        form = TrainingPlanForm(request.POST)
        if form.is_valid():
            training_plan = form.save(commit=False)
            training_plan.trainer = current_trainer
            training_plan.client = client
            training_plan.save()
            
            # ИСПРАВЛЕННАЯ СТРОКА - добавлен namespace
            return redirect('trainerservice:client_details', client_id=client.id)
    else:
        form = TrainingPlanForm()
    
    context = {
        'form': form,
        'client': client,
        'current_trainer': current_trainer
    }
    
    return render(request, 'create_training_plan.html', context)


@login_required
def client_details(request, client_id):
    client = get_object_or_404(User, id=client_id)
    current_trainer = request.user
    
    # Проверяем, что у клиента действительно были тренировки с этим тренером
    has_connection = TrainingPlans.objects.filter(
        trainer=current_trainer, 
        client=client
    ).exists() or ClassClient.objects.filter(
        user=client,
        class_id__trainer=current_trainer
    ).exists()
    
    if not has_connection:
        return redirect('trainerservice:my_clients')
    
    # Получаем тренировочные планы
    training_plans = TrainingPlans.objects.filter(
        trainer=current_trainer,
        client=client
    ).order_by('-is_active', '-id')
    
    # Получаем групповые занятия
    group_classes = ClassClient.objects.filter(
        user=client,
        class_id__trainer=current_trainer
    ).select_related('class_id').order_by('-class_id__starttime')
    
    # Получаем активные подписки
    active_subscriptions = Subscriptions.objects.filter(
        user=client,
        is_active=True
    ).select_related('subscriptiontype')
    
    # Статистика
    total_training_plans = training_plans.count()
    active_training_plans = training_plans.filter(is_active=True).count()
    total_classes = group_classes.count()
    
    # Дата регистрации и стаж - ПРАВИЛЬНЫЙ РАСЧЕТ БЕЗ dateutil
    registration_date = client.date_joined.date()
    today = timezone.now().date()
    
    # Рассчитываем разницу
    total_days = (today - registration_date).days
    
    # Рассчитываем годы, месяцы и дни
    membership_years = total_days // 365
    remaining_days = total_days % 365
    membership_months = remaining_days // 30
    membership_days = remaining_days % 30
    
    context = {
        'client': client,
        'training_plans': training_plans,
        'group_classes': group_classes,
        'active_subscriptions': active_subscriptions,
        'total_training_plans': total_training_plans,
        'active_training_plans': active_training_plans,
        'total_classes': total_classes,
        'registration_date': registration_date,
        'membership_years': membership_years,
        'membership_months': membership_months,
        'membership_days': membership_days,
        'total_days': total_days,
    }
    
    return render(request, 'client_details.html', context)

@login_required
def training_plan_edit_form(request, plan_id):
    training_plan = get_object_or_404(TrainingPlans, id=plan_id, trainer=request.user)
    
    if request.method == 'POST':
        form = TrainingPlanEditForm(request.POST, instance=training_plan)
        if form.is_valid():
            form.save()
            return redirect('trainerservice:client_details', client_id=training_plan.client.id)
    else:
        form = TrainingPlanEditForm(instance=training_plan)
    
    context = {
        'form': form,
        'plan': training_plan,
        'client': training_plan.client
    }
    
    return render(request, 'includes/training_plan_edit_form.html', context)

@login_required
def delete_training_plan(request, plan_id):
    training_plan = get_object_or_404(TrainingPlans, id=plan_id, trainer=request.user)
    client_id = training_plan.client.id
    
    if request.method == 'POST':
        training_plan.delete()
        return redirect('trainerservice:client_details', client_id=client_id)
    
    return redirect('trainerservice:client_details', client_id=client_id)