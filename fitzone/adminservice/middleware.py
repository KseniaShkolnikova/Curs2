# adminservice/middleware.py
from django.db import connection

class UserActionLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            with connection.cursor() as cursor:
                cursor.execute("SET useractions.user_id = %s", [str(request.user.id)])
        
        response = self.get_response(request)
        
        with connection.cursor() as cursor:
            cursor.execute("SET useractions.user_id TO DEFAULT")
        
        return response