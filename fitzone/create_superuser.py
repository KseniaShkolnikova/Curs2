import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fitzone.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
username = os.environ.get('SUPERUSER_USERNAME', 'sesha')
email = os.environ.get('SUPERUSER_EMAIL', 'admin@example.com')
password = os.environ.get('SUPERUSER_PASSWORD', '9003432SAS')

print('Создание пользователя:', username)

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print('✅ Суперпользователь создан')
else:
    print('✅ Суперпользователь уже существует')