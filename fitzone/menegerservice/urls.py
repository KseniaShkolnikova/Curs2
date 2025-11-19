from django.urls import path
from . import views

app_name = 'menegerservice'

urlpatterns = [
    path('', views.manager_home, name='manager_home'),
    path('create-subscription/', views.create_subscription, name='create_subscription'),
    path('subscriptions/<int:subscription_id>/json/', views.subscription_detail_json, name='subscription_detail_json'),
    path('subscriptions/<int:subscription_id>/stats/', views.subscription_stats, name='subscription_stats'),
    path('subscriptions/<int:subscription_id>/edit/', views.edit_subscription, name='edit_subscription'),
    path('subscriptions/delete/', views.delete_subscription, name='delete_subscription'),
    path('reports/', views.reports, name='reports'),
    path('reports/export-csv/', views.export_reports_csv, name='export_reports_csv'),
    path('reports/export-pdf/', views.export_reports_pdf, name='export_reports_pdf'),
    path('subscriptions/', views.subscriptions_list, name='subscriptions_list'),
]

# Добавьте этот код для отладки
def show_urls():
    for url in urlpatterns:
        print(f"URL: {url.pattern}, Name: {url.name}")
    print("All URLs registered successfully!")

show_urls()