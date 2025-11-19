from rest_framework import serializers
from django.contrib.auth.models import User
from clientservice.models import *

class UserProfileSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = UserProfiles
        fields = [
            'id', 'firstname', 'lastname', 'middlename', 'gender',
            'user', 'theme', 'avatar', 'full_name'
        ]

class SubscriptionTypesSerializer(serializers.ModelSerializer):
    included_services = serializers.SerializerMethodField()
    service_icons = serializers.SerializerMethodField()
    
    class Meta:
        model = SubscriptionTypes
        fields = [
            'id', 'name', 'description', 'price', 'durationdays',
            'gym_access', 'group_classes', 'pool_access', 'spa_access',
            'personal_training', 'locker_room', 'towel_service',
            'fitness_consultation', 'nutrition_consultation',
            'guest_visits', 'freeze_days', 'included_services', 'service_icons'
        ]
    
    def get_included_services(self, obj):
        return obj.get_included_services()
    
    def get_service_icons(self, obj):
        return obj.get_service_icons()

class SubscriptionsSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    subscriptiontype = SubscriptionTypesSerializer(read_only=True)
    subscriptiontype_id = serializers.PrimaryKeyRelatedField(
        queryset=SubscriptionTypes.objects.all(), 
        source='subscriptiontype',
        write_only=True
    )
    
    class Meta:
        model = Subscriptions
        fields = [
            'id', 'user', 'subscriptiontype', 'subscriptiontype_id',
            'startdate', 'is_active'
        ]

class TrainingPlansSerializer(serializers.ModelSerializer):
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
    user = serializers.StringRelatedField(read_only=True)
    user_full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = UserActionsLog
        fields = [
            'id', 'user', 'action', 'action_type', 'model_name',
            'object_id', 'details', 'user_full_name', 'actiondate'
        ]

class PaymentsSerializer(serializers.ModelSerializer):
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
        Проверяем, что указан только один из типов платежа
        """
        subscription = data.get('subscription')
        classclient = data.get('classclient')
        
        if not subscription and not classclient:
            raise serializers.ValidationError(
                "Должен быть указан либо subscription, либо classclient"
            )
        
        if subscription and classclient:
            raise serializers.ValidationError(
                "Может быть указан только один тип платежа: subscription ИЛИ classclient"
            )
        
        return data