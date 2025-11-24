from rest_framework import viewsets
from clientservice.models import *
from .serializers import *
from .permission import *

# SUMMARY: ViewSet'ы для REST API системы управления фитнес-клубом
# ОСНОВНОЕ НАЗНАЧЕНИЕ: Предоставление CRUD операций для всех основных моделей системы
# ПРИНЦИП РАБОТЫ: Каждый ViewSet наследуется от ModelViewSet и предоставляет полный набор действий
# СТАНДАРТНАЯ КОНФИГУРАЦИЯ: queryset, serializer_class, permission_classes, pagination_class

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfiles.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [CustomPermission]
    pagination_class = PaginationPage

class SubscriptionTypesViewSet(viewsets.ModelViewSet):
    queryset = SubscriptionTypes.objects.all()
    serializer_class = SubscriptionTypesSerializer
    permission_classes = [CustomPermission]
    pagination_class = PaginationPage

class SubscriptionsViewSet(viewsets.ModelViewSet):
    queryset = Subscriptions.objects.all()
    serializer_class = SubscriptionsSerializer
    permission_classes = [CustomPermission]
    pagination_class = PaginationPage

class TrainingPlansViewSet(viewsets.ModelViewSet):
    queryset = TrainingPlans.objects.all()
    serializer_class = TrainingPlansSerializer
    permission_classes = [CustomPermission]
    pagination_class = PaginationPage

class TrainerSpecializationsViewSet(viewsets.ModelViewSet):
    queryset = TrainerSpecializations.objects.all()
    serializer_class = TrainerSpecializationsSerializer
    permission_classes = [CustomPermission]
    pagination_class = PaginationPage

class ClassesViewSet(viewsets.ModelViewSet):
    queryset = Classes.objects.all()
    serializer_class = ClassesSerializer
    permission_classes = [CustomPermission]
    pagination_class = PaginationPage

class ClassClientViewSet(viewsets.ModelViewSet):
    queryset = ClassClient.objects.all()
    serializer_class = ClassClientSerializer
    permission_classes = [CustomPermission]
    pagination_class = PaginationPage

class UserActionsLogViewSet(viewsets.ModelViewSet):
    queryset = UserActionsLog.objects.all()
    serializer_class = UserActionsLogSerializer
    permission_classes = [CustomPermission]
    pagination_class = PaginationPage

class PaymentsViewSet(viewsets.ModelViewSet):
    queryset = Payments.objects.all()
    serializer_class = PaymentsSerializer
    permission_classes = [CustomPermission]
    pagination_class = PaginationPage