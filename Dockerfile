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

CMD ["sh", "-c", "cd /app/fitzone && echo '=== ПЕРЕМЕННЫЕ ===' && echo 'DATABASE_URL: $DATABASE_URL' && echo '⏳ Ожидаем БД...' && python -c \"\nimport os\nimport time\nfrom urllib.parse import urlparse\n\ndb_url = os.environ.get('DATABASE_URL')\nif db_url:\n    parsed = urlparse(db_url)\n    host = parsed.hostname\n    port = parsed.port or 5432\n    user = parsed.username\n    password = parsed.password\n    dbname = parsed.path[1:] if parsed.path else 'postgres'\n    \n    import psycopg2\n    for i in range(30):  # 30 попыток по 2 секунды = 60 секунд\n        try:\n            conn = psycopg2.connect(\n                host=host,\n                port=port,\n                user=user,\n                password=password,\n                dbname=dbname\n            )\n            conn.close()\n            print('✅ БД готова!')\n            break\n        except Exception as e:\n            if i == 0:\n                print(f'Ожидаем БД: {e}')\n            time.sleep(2)\n    else:\n        print('❌ Не удалось подключиться к БД за 60 секунд')\nelse:\n    print('❌ Нет DATABASE_URL')\n\" && python manage.py migrate && gunicorn fitzone.wsgi:application --bind 0.0.0.0:8000 --workers 3"]