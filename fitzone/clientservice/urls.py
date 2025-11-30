from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('home/', views.home_view, name='home'),
    path('classes/', views.classes_view, name='classes'),
    path('profile/', views.profile_view, name='profile'),
    path('subscription/', views.subscription_view, name='subscription'),
    path('', views.login_view, name='login'),
    path('registration/', views.register_view, name='registration'),
    path('logout/', views.logout_user, name='logout'),
    path('subscriptions/<int:subscription_id>/', views.subscription_detail, name='detail_subscription'),
    path('<int:subscription_id>/payment/', views.subscription_payment, name='subscription_payment'),
    path('process-payment/<int:subscription_id>/', views.process_payment, name='process_payment'),
    path('classes/booking/<int:class_id>/', views.class_booking, name='class_booking'),
    path('classes/payment/<int:class_id>/', views.process_class_payment, name='process_class_payment'),
    path('personal-training/', views.personal_training, name='personal_training'),
    path('book-personal-training/<int:trainer_id>/', views.book_personal_training, name='book_personal_training'),
    path('process-personal-payment/<int:trainer_id>/', views.process_personal_payment, name='process_personal_payment'),
    path('password-reset/', views.password_reset_view, name='password_reset'),
path('subscription/agreement/<int:payment_id>/', 
         views.generate_subscription_agreement, 
         name='subscription_agreement'),
    path('deactivate-account/', views.deactivate_account, name='deactivate_account'),

             path('buy-personal-package/<int:trainer_id>/', views.buy_personal_package, name='buy_personal_package'),
path('test-email/', views.test_resend_email, name='test_email'),
         # В urls.py
path('generate-payment-document/<int:payment_id>/', views.generate_payment_document, name='generate_payment_document'),
    # Добавь эти два URL
    path('create-personal-training/<int:trainer_id>/', views.create_personal_training, name='create_personal_training'),
path('cancel-subscription/<int:subscription_id>/', views.cancel_subscription, name='cancel_subscription'),
    path('cancel-training/<int:class_id>/', views.cancel_training, name='cancel_training')]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)