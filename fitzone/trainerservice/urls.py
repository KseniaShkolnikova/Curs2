from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'trainerservice'

urlpatterns = [
    path('', views.home, name='trainer_home'),
    path('trainer_classes/', views.trainer_classes, name='trainer_classes'),
    path('trainer_classes/create/', views.create_class, name='create_trainer_classes'),
    path('trainer_classes/<int:class_id>/delete/', views.delete_class, name='delete_trainer_classes'),
    path('trainer_classes/<int:class_id>/edit/', views.edit_class, name='edit_class'),
    path('trainer_classes/<int:class_id>/cancel/', views.cancel_class, name='cancel_class'),
    path('client/<int:client_id>/', views.client_details, name='client_details'),
    path('client/<int:client_id>/create-plan/', views.create_training_plan, name='create_training_plan'),
    path('training-plan/<int:plan_id>/edit/', views.training_plan_edit_form, name='training_plan_edit_form'),
    path('training-plan/<int:plan_id>/delete/', views.delete_training_plan, name='delete_training_plan'),
    path('trainer_classes/<int:class_id>/', views.get_class_data, name='get_class_data'),
    path('my-clients/', views.my_clients, name='my_clients')
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)