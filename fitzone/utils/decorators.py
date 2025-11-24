# utils/decorators.py
from django.shortcuts import render
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required

def client_required(view_func):
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.groups.filter(name='Клиент').exists():
            return render(request, '403.html', status=403)
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def trainer_required(view_func):
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.groups.filter(name='Тренер').exists():
            return render(request, '403.html', status=403)
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def manager_required(view_func):
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.groups.filter(name='Менеджер по продажам').exists():
            return render(request, '403.html', status=403)
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def admin_required(view_func):
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.groups.filter(name='Администратор').exists():
            return render(request, '403.html', status=403)
        return view_func(request, *args, **kwargs)
    return _wrapped_view