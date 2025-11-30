from rest_framework import permissions
from rest_framework.pagination import PageNumberPagination


class CustomPermission(permissions.DjangoModelPermissions):
    """
    Кастомный класс разрешений для Django REST Framework.
    Расширяет стандартные DjangoModelPermissions с переопределенным perms_map
    для более точного контроля прав доступа к API endpoints.
    """
    
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],  # Права на просмотр информации
        'OPTIONS': ['%(app_label)s.view_%(model_name)s'],  # Права на получение информации о доступных методах
        'HEAD': ['%(app_label)s.view_%(model_name)s'],  # Права на просмотр информации 
        'POST': ['%(app_label)s.add_%(model_name)s'],  # Права на создание новых записей
        'PUT': ['%(app_label)s.change_%(model_name)s'],  # Права на полное изменение данных
        'PATCH': ['%(app_label)s.change_%(model_name)s'],  # Права на частичное изменение данных
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],  # Права на удаление записей
    }
    

class PaginationPage(PageNumberPagination):
    """
    Кастомный класс пагинации для API.
    Наследуется от PageNumberPagination и настраивает параметры пагинации
    для обеспечения гибкого управления размером страниц и номером страницы.
    """
    
    page_size_query_param = 'page_size'  # Параметр запроса для указания размера страницы
    page_query_param = 'page'  # Параметр запроса для указания номера страницы
    page_size = 20  # Размер страницы по умолчанию (количество элементов на странице)