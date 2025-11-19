from django.contrib import admin
from .models import *

@admin.register(UserProfiles)
class UserProfilesAdmin(admin.ModelAdmin):
    pass

@admin.register(SubscriptionTypes)
class SubscriptionTypesAdmin(admin.ModelAdmin):
    pass

@admin.register(Subscriptions)
class SubscriptionsAdmin(admin.ModelAdmin):
    pass

@admin.register(TrainingPlans)
class TrainingPlansAdmin(admin.ModelAdmin):
    pass

@admin.register(TrainerSpecializations)
class TrainerSpecializationsAdmin(admin.ModelAdmin):
    pass

@admin.register(Classes)
class ClassesAdmin(admin.ModelAdmin):
    pass

@admin.register(ClassClient)
class ClassClientAdmin(admin.ModelAdmin):
    pass

@admin.register(UserActionsLog)
class UserActionsLogAdmin(admin.ModelAdmin):
    pass

@admin.register(Payments)
class PaymentsAdmin(admin.ModelAdmin):
    pass