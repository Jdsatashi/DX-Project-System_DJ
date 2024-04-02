from functools import wraps

from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render
from rest_framework import permissions


def quyen(model, method):
    model_content = ContentType.objects.get_for_model(model)

    required_perm = f"{method}_{model_content.app_label}_{model_content.model}"

    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                ctx = {'message': "Bạn chưa đăng nhập."}
                return render(request, 'errors/403.html', ctx)
            if not request.user.has_quyen(required_perm):
                ctx = {'message': "Bạn không có quyền truy cập vào trang này."}
                return render(request, 'errors/403.html', ctx)
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


class ValidateQuyenRest(permissions.BasePermission):
    """
    ValidateQuyenRest is a custom permission for Rest Framework API, use functools.partial to add attribute.
    Example: partial(ValidateQuyenRest, model=models.Test)
    """
    def __init__(self, model):
        super().__init__()
        self.model = model

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
        content_type = ContentType.objects.get_for_model(self.model)

        required_permission = f'{action}_{module_name}_{content_type.model}'
        print(required_permission)
        print(f"Checking quyền: {user.has_quyen(required_permission)}")
        print(f"Checking permission: {user.has_perm(required_permission)}")
        return user.has_quyen(required_permission)
