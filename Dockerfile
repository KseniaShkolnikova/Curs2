FROM python:3.11-slim

# Установка системных зависимостей для PostgreSQL и других пакетов
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    pkg-config \
    libcairo2-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем requirements.txt
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY fitzone/ .

# Создаем директории для статики и медиа
RUN mkdir -p staticfiles media

# Собираем статические файлы
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "fitzone.wsgi:application", "--bind", "0.0.0.0:8000"]