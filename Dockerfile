FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    gcc python3-dev libpq-dev pkg-config libcairo2-dev postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# ПРОВЕРКА: что файлы скопировались
RUN echo "=== ПРОВЕРКА ФАЙЛОВ ===" && \
    ls -la && \
    echo "=== db_backup.sql ===" && \
    if [ -f db_backup.sql ]; then \
        echo "✅ db_backup.sql найден, размер: $(wc -l < db_backup.sql) строк"; \
    else \
        echo "❌ db_backup.sql НЕ НАЙДЕН!"; \
        echo "Доступные файлы:"; \
        find . -name "*.sql" -type f; \
    fi

RUN mkdir -p staticfiles media

RUN cd /app/fitzone && python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["sh", "-c", "cd /app/fitzone && echo '⏳ Ожидаем БД...' && until psql \"$DATABASE_URL\" -c 'SELECT 1;' >/dev/null 2>&1; do sleep 2; done && echo '✅ БД готова!' && python manage.py migrate && if [ -f /app/db_backup.sql ] && [ -s /app/db_backup.sql ]; then echo '🔄 Восстанавливаем дамп...' && psql \"$DATABASE_URL\" < /app/db_backup.sql && echo '✅ Дамп восстановлен!'; else echo '⚠️ Дамп не найден или пустой'; fi && gunicorn fitzone.wsgi:application --bind 0.0.0.0:8000 --workers 3"]