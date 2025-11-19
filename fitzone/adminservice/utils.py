# adminservice/utils.py
from django.db import connection
from contextlib import contextmanager

@contextmanager
def set_user_context(user_id):
    """
    Контекстный менеджер для установки user_id в контексте БД
    """
    with connection.cursor() as cursor:
        try:
            # Устанавливаем user_id в контекст PostgreSQL
            cursor.execute("SET LOCAL useractions.user_id = %s", [str(user_id)])
            yield
        finally:
            # Очищаем контекст
            cursor.execute("RESET useractions.user_id")