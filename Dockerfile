FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    gcc python3-dev libpq-dev pkg-config libcairo2-dev postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория - корень
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p staticfiles media

# Собираем статику
RUN cd fitzone && python manage.py collectstatic --noinput

EXPOSE 8000

# ПРОСТАЯ команда запуска
CMD ["sh", "-c", "cd /FITZONE/fitzone && gunicorn fitzone.wsgi:application --bind 0.0.0.0:8000 --workers 3"]