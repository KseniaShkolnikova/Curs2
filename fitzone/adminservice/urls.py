from django.urls import path
from . import views

app_name = 'adminservice'

urlpatterns = [
    # Основные маршруты админ-панели
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('action-logs/', views.action_logs, name='action_logs'),
    
    # Управление бэкапами
    path('backup-management/', views.backup_management, name='backup_management'),
    path('create-backup/', views.create_backup, name='create_backup'),
    path('restore-backup/', views.restore_backup, name='restore_backup'),
    
    # Экспорт/импорт данных
    path('export-payments/', views.export_payments, name='export_payments'),
    path('import-trainers/', views.import_trainers, name='import_trainers'),
    
    # Управление персоналом (CRUD операции)
    path('staff-management/', views.staff_management, name='staff_management'),
    path('create-staff/', views.create_staff, name='create_staff'),
    path('get-staff-data/<int:user_id>/', views.get_staff_data, name='get_staff_data'),
    path('update-staff/<int:user_id>/', views.update_staff, name='update_staff'),
    path('delete-staff/<int:user_id>/', views.delete_staff, name='delete_staff'),
]