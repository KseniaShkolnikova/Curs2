"""
URL configuration for fitzone project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.contrib.auth import get_user_model
from django.http import HttpResponse

def create_superuser_view(request):
    User = get_user_model()
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'your_password_123')
        return HttpResponse('''
            <h1>✅ Суперпользователь создан!</h1>
            <p>Логин: <strong>admin</strong></p>
            <p>Пароль: <strong>your_password_123</strong></p>
            <p><a href="/admin/">Перейти в админку</a></p>
        ''')
    return HttpResponse('✅ Суперпользователь уже существует')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('clientservice.urls')),
    path('meneger/', include('menegerservice.urls')),
    path('trainer/', include('trainerservice.urls')),
     path('admin-panel/', include('adminservice.urls')),
     path('create-superuser/', create_superuser_view),
     path('api/', include('api.urls'))

]
