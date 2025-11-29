FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    gcc python3-dev libpq-dev pkg-config libcairo2-dev postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# ОТЛАДКА: смотрим структуру папок
RUN echo "=== Содержимое /app ===" && ls -la && \
    echo "=== Поиск manage.py ===" && find /app -name "manage.py" -type f

RUN mkdir -p staticfiles media

# Автоматически находим manage.py и собираем статику
RUN find /app -name "manage.py" -execdir python manage.py collectstatic --noinput \;

EXPOSE 8000

# Автоматически находим manage.py при запуске
CMD find /app -name "manage.py" -execdir python manage.py migrate \\; && \
    find /app -name "manage.py" -execdir gunicorn fitzone.wsgi:application --bind 0.0.0.0:8000 --workers 3 \\;