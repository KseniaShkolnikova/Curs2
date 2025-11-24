from .views import *
from rest_framework import routers

urlpatterns = [
    
]

# SUMMARY: Регистрация ViewSet'ов для REST API endpoints
# ОСНОВНОЕ НАЗНАЧЕНИЕ: Автоматическая генерация URL маршрутов для всех моделей системы
# ПРИНЦИП РАБОТЫ: Router создает стандартные CRUD endpoints (list, create, retrieve, update, destroy)
# СТРУКТУРА: Каждый ViewSet предоставляет полный API для соответствующей модели

router = routers.SimpleRouter()
router.register('user-profiles', UserProfileViewSet, basename='user-profiles')
router.register('subscription-types', SubscriptionTypesViewSet, basename='subscription-types')
router.register('subscriptions', SubscriptionsViewSet, basename='subscriptions')
router.register('training-plans', TrainingPlansViewSet, basename='training-plans')
router.register('trainer-specializations', TrainerSpecializationsViewSet, basename='trainer-specializations')
router.register('classes', ClassesViewSet, basename='classes')
router.register('class-client', ClassClientViewSet, basename='class-client')
router.register('user-actions-log', UserActionsLogViewSet, basename='user-actions-log')
router.register('payments', PaymentsViewSet, basename='payments')

urlpatterns += router.urls