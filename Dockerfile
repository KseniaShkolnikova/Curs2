FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    pkg-config \
    libcairo2-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем requirements.txt
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект включая дамп БД
COPY . .

# Создаем директории для статики и медиа
RUN mkdir -p staticfiles media

# Собираем статику
RUN python manage.py collectstatic --noinput

EXPOSE 8000

# Создаем скрипт для инициализации БД
RUN echo '#!/bin/bash\n\
python manage.py migrate\n\
if [ -f db_backup.sql ]; then\n\
  echo "Восстанавливаем базу данных из дампа..."\n\
  PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME < db_backup.sql\n\
fi\n\
gunicorn fitzone.wsgi:application --bind 0.0.0.0:8000' > /app/start.sh

RUN chmod +x /app/start.sh

CMD ["/bin/bash", "/app/start.sh"]