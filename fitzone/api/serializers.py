from rest_framework import serializers
from django.contrib.auth.models import User
from clientservice.models import *

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Сериализатор для профилей пользователей.
    Включает вычисляемое поле full_name и связанного пользователя.
    """
    user = serializers.StringRelatedField(read_only=True)
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = UserProfiles
        fields = [
            'id', 'firstname', 'lastname', 'middlename', 'gender',
            'user', 'theme', 'avatar', 'full_name'
        ]

class SubscriptionTypesSerializer(serializers.ModelSerializer):
    """
    Сериализатор для типов подписок.
    Включает вычисляемые поля для включенных услуг и их иконок.
    """
    included_services = serializers.SerializerMethodField()
    service_icons = serializers.SerializerMethodField()
    
    class Meta:
        model = SubscriptionTypes
        fields = [
            'id', 'name', 'description', 'price', 'durationdays',
            'gym_access',  'pool_access', 'spa_access',
             'locker_room', 'towel_service',
             'nutrition_consultation',
             'included_services', 'service_icons'
        ]
    
    def get_included_services(self, obj):
        """Получает список включенных услуг для типа подписки"""
        return obj.get_included_services()
    
    def get_service_icons(self, obj):
        """Получает список иконок для услуг типа подписки"""
        return obj.get_service_icons()

class SubscriptionsSerializer(serializers.ModelSerializer):
    """
    Сериализатор для подписок пользователей.
    Поддерживает чтение полного объекта subscriptiontype и запись по ID.
    """
    user = serializers.StringRelatedField(read_only=True)
    subscriptiontype = SubscriptionTypesSerializer(read_only=True)
    subscriptiontype_id = serializers.PrimaryKeyRelatedField(
        queryset=SubscriptionTypes.objects.all(), 
        source='subscriptiontype',
        write_only=True
    )
    # ДОБАВЬТЕ ЭТО ПОЛЕ:
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source='user', 
        write_only=True
    )
    
    class Meta:
        model = Subscriptions
        fields = [
            'id', 'user', 'user_id', 'subscriptiontype', 'subscriptiontype_id',  # Добавлен user_id
            'startdate', 'is_active'
        ]

class TrainingPlansSerializer(serializers.ModelSerializer):
    """
    Сериализатор для тренировочных планов.
    Включает связанных тренера и клиента с поддержкой записи по ID.
    """
    trainer = serializers.StringRelatedField(read_only=True)
    client = serializers.StringRelatedField(read_only=True)
    trainer_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source='trainer',
        write_only=True
    )
    client_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source='client',
        write_only=True
    )
    
    class Meta:
        model = TrainingPlans
        fields = [
            'id', 'trainer', 'trainer_id', 'client', 'client_id',
            'name', 'description', 'is_active'
        ]

class TrainerSpecializationsSerializer(serializers.ModelSerializer):
    """
    Сериализатор для специализаций тренеров.
    """
    trainer = serializers.StringRelatedField(read_only=True)
    trainer_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source='trainer',
        write_only=True
    )
    
    class Meta:
        model = TrainerSpecializations
        fields = ['id', 'trainer', 'trainer_id', 'specialization']

class ClassesSerializer(serializers.ModelSerializer):
    """
    Сериализатор для групповых занятий.
    """
    trainer = serializers.StringRelatedField(read_only=True)
    trainer_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source='trainer',
        write_only=True
    )
    
    class Meta:
        model = Classes
        fields = [
            'id', 'trainer', 'trainer_id', 'name', 'description',
            'starttime', 'endtime', 'maxclient', 'price', 'is_active'
        ]

class ClassClientSerializer(serializers.ModelSerializer):
    """
    Сериализатор для связи клиентов с групповыми занятиями.
    """
    class_id = ClassesSerializer(read_only=True)
    user = serializers.StringRelatedField(read_only=True)
    class_id_id = serializers.PrimaryKeyRelatedField(
        queryset=Classes.objects.all(), 
        source='class_id',
        write_only=True
    )
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source='user',
        write_only=True
    )
    
    class Meta:
        model = ClassClient
        fields = [
            'id', 'class_id', 'class_id_id', 'user', 'user_id',
            'amount', 'is_active'
        ]

class UserActionsLogSerializer(serializers.ModelSerializer):
    """
    Сериализатор для логов действий пользователей.
    Включает вычисляемое поле с полным именем пользователя.
    """
    user = serializers.StringRelatedField(read_only=True)
    user_full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = UserActionsLog
        fields = [
            'id', 'user', 'action', 'action_type', 'model_name',
            'object_id', 'details', 'user_full_name', 'actiondate'
        ]

class PaymentsSerializer(serializers.ModelSerializer):
    """
    Сериализатор для платежей.
    Поддерживает два типа платежей: за подписки и за групповые занятия.
    Включает валидацию для обеспечения только одного типа платежа.
    """
    subscription = SubscriptionsSerializer(read_only=True)
    classclient = ClassClientSerializer(read_only=True)
    subscription_id = serializers.PrimaryKeyRelatedField(
        queryset=Subscriptions.objects.all(), 
        source='subscription',
        write_only=True,
        required=False,
        allow_null=True
    )
    classclient_id = serializers.PrimaryKeyRelatedField(
        queryset=ClassClient.objects.all(), 
        source='classclient',
        write_only=True,
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Payments
        fields = [
            'id', 'subscription', 'subscription_id', 'classclient', 'classclient_id',
            'price', 'paymentdate'
        ]
    
    def validate(self, data):
        """
        Проверяет, что указан только один из типов платежа: подписка ИЛИ групповое занятие.
        Вызывает ValidationError если оба типа указаны или ни один не указан.
        """
        subscription = data.get('subscription')
        classclient = data.get('classclient')
        
        # Проверка что указан хотя бы один тип платежа
        if not subscription and not classclient:
            raise serializers.ValidationError(
                "Должен быть указан либо subscription, либо classclient"
            )
        
        # Проверка что не указаны оба типа одновременно
        if subscription and classclient:
            raise serializers.ValidationError(
                "Может быть указан только один тип платежа: subscription ИЛИ classclient"
            )
        
        return data