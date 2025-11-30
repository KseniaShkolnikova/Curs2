FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    gcc python3-dev libpq-dev pkg-config libcairo2-dev postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p staticfiles media

RUN cd /app/fitzone && python manage.py collectstatic --noinput

EXPOSE 8000

# ПРОСТОЙ И РАБОЧИЙ CMD
CMD cd /app/fitzone && python manage.py migrate && python -c "import os; import django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fitzone.settings'); django.setup(); from django.contrib.auth import get_user_model; User = get_user_model(); username = os.environ.get('SUPERUSER_USERNAME', 'sesha'); email = os.environ.get('SUPERUSER_EMAIL', 'admin@example.com'); password = os.environ.get('SUPERUSER_PASSWORD', '9003432SAS'); print(f'Создание пользователя: {username}'); if not User.objects.filter(username=username).exists(): User.objects.create_superuser(username, email, password); print('✅ Суперпользователь создан'); else: print('✅ Суперпользователь уже существует')" && gunicorn fitzone.wsgi:application --bind 0.0.0.0:8000 --workers 3