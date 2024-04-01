import inspect
from functools import wraps

from django.apps import apps
from django.shortcuts import render
from django.contrib.contenttypes.models import ContentType
from django.urls import resolve
from rest_framework import permissions

from account.models import Quyen


def quyen(required_permissions):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not request.user.has_perm(required_permissions):
                ctx = {'message': "Bạn không có quyền truy cập vào trang này."}
                return render(request, 'errors/403.html', ctx)
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


class ValidateQuyenRest(permissions.BasePermission):
    def __init__(self, model_name):
        super().__init__()
        self.model_name = model_name

    def has_permission(self, request, view):
        # Authenticate
        user = request.user
        if not user.is_authenticated:
            return False
        # Get module_name
        try:
            view_func = getattr(view, view.action)
        except AttributeError:
            view_func = None
        try:
            module_name = view_func.__qualname__.split('.')[2]  # Lấy phần tên nằm ở vị trí thứ 3
        except IndexError:
            module_name = view.__module__.split('.')[0]
        print("---------- TEST ----------")
        print(f"view_func: {view_func}")
        print(f"module_name: {module_name}")
        # Get action of function
        action = view.action
        model_name = apps.get_model(module_name, self.model_name)
        content_type = ContentType.objects.get_for_model(model_name)

        required_permission = f'{action}_{module_name}_{content_type.model}'
        print(required_permission)
        print(f"Checking quyền: {user.has_quyen(required_permission)}")
        print(f"Checking permission: {user.has_perm(required_permission)}")
        return user.has_perm(required_permission)
