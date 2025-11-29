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

# Копируем весь проект
COPY . .

# Создаем директории для статики и медиа
RUN mkdir -p staticfiles media

# Собираем статику (правильный путь)
RUN cd FitZone/fitzone && python manage.py collectstatic --noinput

EXPOSE 8000

# Скрипт запуска с правильными путями
RUN echo '#!/bin/bash\n\
set -e\n\
echo "=== Запуск приложения ==="\n\
\n\
echo "1. Проверяем подключение к БД..."\n\
until PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT 1;" > /dev/null 2>&1; do\n\
  echo "Ждем подключения к БД..."\n\
  sleep 2\n\
done\n\
\n\
echo "2. Применяем миграции..."\n\
cd FitZone/fitzone && python manage.py migrate\n\
\n\
echo "3. Проверяем наличие дампа БД..."\n\
if [ -f db_backup.sql ] && [ -s db_backup.sql ]; then\n\
  echo "Размер дампа: $(wc -l < db_backup.sql) строк"\n\
  echo "Восстанавливаем базу данных из дампа..."\n\
  PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME < db_backup.sql\n\
  echo "✅ База восстановлена из дампа!"\n\
else\n\
  echo "⚠️ Дамп БД не найден или пустой, работаем с текущей БД"\n\
fi\n\
\n\
echo "4. Запускаем Gunicorn..."\n\
cd FitZone/fitzone && exec gunicorn fitzone.wsgi:application --bind 0.0.0.0:8000 --workers 3' > /app/start.sh

RUN chmod +x /app/start.sh

CMD ["/bin/bash", "/app/start.sh"]