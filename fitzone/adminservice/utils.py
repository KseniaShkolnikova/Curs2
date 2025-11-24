from django.db import connection
from contextlib import contextmanager

@contextmanager
def set_user_context(user_id):
    """
    SUMMARY: Контекстный менеджер для установки идентификатора пользователя в контексте базы данных
    
    ОСНОВНОЕ НАЗНАЧЕНИЕ:
    - Устанавливает user_id в переменной useractions.user_id для отслеживания действий пользователя
    - Автоматически сбрасывает контекст после выполнения блока кода
    - Используется для аудита и логирования действий в БД
    
    ПРИНЦИП РАБОТЫ:
    1. Устанавливает значение user_id в PostgreSQL-переменную useractions.user_id
    2. Выполняет код внутри блока with с установленным контекстом
    3. Гарантированно сбрасывает контекст даже при возникновении исключений
    
    ПАРАМЕТРЫ:
    - user_id: идентификатор пользователя для установки в контекст БД
    """
    with connection.cursor() as cursor:
        try:
            # SUMMARY: Установка user_id в контекст PostgreSQL
            cursor.execute("SET LOCAL useractions.user_id = %s", [str(user_id)])
            yield
        finally:
            # SUMMARY: Гарантированное восстановление исходного состояния контекста
            cursor.execute("RESET useractions.user_id")