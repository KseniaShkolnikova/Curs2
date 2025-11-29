FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    gcc python3-dev libpq-dev pkg-config libcairo2-dev postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p staticfiles media

# Собираем статику (теперь знаем точный путь)
RUN cd /app/fitzone && python manage.py collectstatic --noinput

EXPOSE 8000


# ПРОСТОЙ и РАБОЧИЙ CMD
CMD ["sh", "-c", "cd /app/fitzone && python manage.py migrate && if [ -f /app/db_backup.sql ]; then psql $DATABASE_URL < /app/db_backup.sql; echo '✅ База восстановлена из дампа'; fi && gunicorn fitzone.wsgi:application --bind 0.0.0.0:8000 --workers 3"]