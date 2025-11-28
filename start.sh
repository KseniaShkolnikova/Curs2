python manage.py migrate
python manage.py collectstatic --noinput
gunicorn fitzone.wsgi:application --bind 0.0.0.0:$PORT