FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    gcc python3-dev libpq-dev postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p staticfiles media

# Теперь знаем точный путь!
RUN cd fitzone && python manage.py collectstatic --noinput

EXPOSE 8000

RUN echo '#!/bin/bash\n\
set -e\n\
echo "=== Запуск приложения ===\n\
\n\
# Переходим в папку проекта\n\
cd fitzone\n\
\n\
echo "1. Проверяем БД..."\n\
until PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT 1;" > /dev/null 2>&1; do\n\
  echo "Ждем БД..." && sleep 2\ndone\n\
\n\
echo "2. Миграции..."\n\
python manage.py migrate\n\
\n\
echo "3. Восстановление БД..."\n\
if [ -f /app/db_backup.sql ] && [ -s /app/db_backup.sql ]; then\n\
  echo "Восстанавливаем из дампа..."\n\
  PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME < /app/db_backup.sql\n\
  echo "✅ Готово!"\n\
fi\n\
\n\
echo "4. Запуск Gunicorn..."\n\
exec gunicorn fitzone.wsgi:application --bind 0.0.0.0:8000 --workers 3' > /app/start.sh

RUN chmod +x /app/start.sh

CMD ["/bin/bash", "/app/start.sh"]