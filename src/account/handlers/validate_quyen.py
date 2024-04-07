from functools import wraps

from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render
from rest_framework import permissions

from account.models import Quyen


def quyen(model, method):
    """ quyen use as class method @quyen for view function"""
    model_content = "ContentType.objects.get_for_model(model)"

    # Create decorator function
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            # Get string quyen name
            required_perm = f"{method}_{model_content.app_label}_{model_content.model}"
            # Get primary key if exist
            pk = kwargs.get('pk')
            # Check authenticate
            if not request.user.is_authenticated:
                ctx = {'message': "Bạn chưa đăng nhập."}
                return render(request, 'errors/403.html', ctx)
            # Block message
            ctx = {'message': "Bạn không có quyền truy cập vào trang này."}
            # Check user has quyen
            check_quyen = request.user.has_quyen(required_perm)
            # Return when false
            if not check_quyen:
                return render(request, 'errors/403.html', ctx)
            # If user has quyen, check PK
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
        modules = view.__module__.split('.')
        contents_type = ContentType.objects.values_list('app_label', flat=True).distinct()
        module_name = ''
        for module in modules:
            if module in contents_type:
                module_name = module
                break

        object_pk = view.kwargs.get('pk', None)
        # Get action of function
        action = view.action
        content_type = ContentType.objects.get_for_model(self.model)
        # Merge string from above data to generated permission name
        required_permission = f'{action}_{module_name}_{content_type.model}'
        # Check if user or user_nhom has quyen
        user_nhom_perm = user.has_nhom_with_quyen(required_permission)
        user_perm = user.has_quyen(required_permission)
        # Check if object has PK
        if object_pk is not None:
            # Add PK to string quyen
            required_permission = f"{required_permission}_{object_pk}"
            # Checking quyen with PK is exist
            quyen = quyen_exist({'name': required_permission})
            # If quyen PK exist, handling validate quyen user
            if quyen is not None:
                # Check if user or user_nhom has quyen PK
                user_perm = user.is_allow(required_permission)
                user_nhom_perm = user.has_nhom_with_quyen(required_permission)
                # If user or nhom user has quyen, return True
                return user_nhom_perm or user_perm
            # Return True (not required quyen) when object with PK doesn't required Quyen PK
            return True
        # If user or nhom user has quyen, return True
        return user_nhom_perm or user_perm


def quyen_exist(quyen: dict):
    # Validate quyen is dictionary and quyen has value
    if not isinstance(quyen, dict) or quyen is None:
        raise ValueError("quyen must be a dictionary {'key': value}.")

    q = Quyen.objects.filter(name=quyen.get('name'))
    return q.first() if q.exists() else None
