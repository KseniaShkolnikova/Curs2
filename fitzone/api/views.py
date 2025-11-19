from rest_framework import viewsets
from clientservice.models import *
from .serializers import *

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfiles.objects.all()
    serializer_class = UserProfileSerializer

class SubscriptionTypesViewSet(viewsets.ModelViewSet):
    queryset = SubscriptionTypes.objects.all()
    serializer_class = SubscriptionTypesSerializer

class SubscriptionsViewSet(viewsets.ModelViewSet):
    queryset = Subscriptions.objects.all()
    serializer_class = SubscriptionsSerializer

class TrainingPlansViewSet(viewsets.ModelViewSet):
    queryset = TrainingPlans.objects.all()
    serializer_class = TrainingPlansSerializer

class TrainerSpecializationsViewSet(viewsets.ModelViewSet):
    queryset = TrainerSpecializations.objects.all()
    serializer_class = TrainerSpecializationsSerializer

class ClassesViewSet(viewsets.ModelViewSet):
    queryset = Classes.objects.all()
    serializer_class = ClassesSerializer

class ClassClientViewSet(viewsets.ModelViewSet):
    queryset = ClassClient.objects.all()
    serializer_class = ClassClientSerializer

class UserActionsLogViewSet(viewsets.ModelViewSet):
    queryset = UserActionsLog.objects.all()
    serializer_class = UserActionsLogSerializer

class PaymentsViewSet(viewsets.ModelViewSet):
    queryset = Payments.objects.all()
    serializer_class = PaymentsSerializer