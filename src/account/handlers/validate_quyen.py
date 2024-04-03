from functools import wraps

from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render
from rest_framework import permissions

from account.models import Quyen


def quyen(model, method):
    """ quyen use as class method @quyen for view function"""
    model_content = ContentType.objects.get_for_model(model)

    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            required_perm = f"{method}_{model_content.app_label}_{model_content.model}"
            pk = kwargs.get('pk')
            if not request.user.is_authenticated:
                ctx = {'message': "Bạn chưa đăng nhập."}
                return render(request, 'errors/403.html', ctx)
            ctx = {'message': "Bạn không có quyền truy cập vào trang này."}
            check_quyen = request.user.has_quyen(required_perm)
            if not check_quyen:
                return render(request, 'errors/403.html', ctx)
            if pk:
                required_perm = f"{required_perm}_{pk}"
                if not check_quyen and not request.user.has_quyen(required_perm):
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
            module_name = view_func.__qualname__.split('.')[2]
        except IndexError:
            module_name = view.__module__.split('.')[0]
        print("---------- TEST ----------")
        object_pk = view.kwargs.get('pk', None)
        print(f"object_pk: {object_pk}")
        # Get action of function
        action = view.action
        content_type = ContentType.objects.get_for_model(self.model)

        required_permission = f'{action}_{module_name}_{content_type.model}'
        print(f"Required perm 1: {required_permission}")
        model_permission = user.has_quyen(required_permission)
        if object_pk is not None:
            print(f"Object pk is not None")
            required_permission = f"{required_permission}_{object_pk}"
            print(f"Required perm 2: {required_permission}")
            quyen = quyen_exist({'name': required_permission})
            print(f"Quyen: {quyen}")
            if quyen is not None:
                is_allow = user.is_allow(required_permission)
                print(f"is_allow: {is_allow}")
                return is_allow
            return True
        print(f"Return model permission")
        return model_permission


def quyen_exist(quyen: dict):
    if not isinstance(quyen, dict) or quyen is None:
        raise ValueError("quyen must be a dictionary {'key': value}.")
    q = Quyen.objects.filter(name=quyen.get('name'))
    return q.first() if q.exists() else None
