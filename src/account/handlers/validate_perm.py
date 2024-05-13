import time
from functools import wraps

from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render
from rest_framework import permissions

from utils.perms.check import perm_exist, user_has_perm


def perm(model, method):
    """ perm use as class method @perm for view function"""
    model_content = "ContentType.objects.get_for_model(model)"

    # Create decorator function
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            # Get string perm name
            required_perm = f"{method}_{model_content.app_label}_{model_content.model}"
            # Get primary key if exist
            pk = kwargs.get('pk')
            # Check authenticate
            if not request.user.is_authenticated:
                ctx = {'message': "Bạn chưa đăng nhập."}
                return render(request, 'errors/403.html', ctx)
            # Block message
            ctx = {'message': "Bạn không có quyền truy cập vào trang này."}
            # Check user has perm
            check_perm = request.user.is_perm(required_perm)
            # Return when false
            if not check_perm:
                return render(request, 'errors/403.html', ctx)
            # If user has perm, check PK
            if pk:
                required_perm = f"{required_perm}_{pk}"
                if not check_perm and not request.user.is_perm(required_perm):
                    return render(request, 'errors/403.html', ctx)
            return view_func(request, *args, **kwargs)

        return wrapped_view

    return decorator


class ValidatePermRest(permissions.BasePermission):
    """
    ValidatePermRest is a custom permission for Rest Framework API, use functools.partial to add attribute.
    Example: partial(ValidatePermRest, model=models.Test)
    """

    def __init__(self, model):
        super().__init__()
        self.model = model

    def has_permission(self, request, view):
        start_time = time.time()
        print(f"----- REQUEST PATH: {request.path}")
        # Allow showing on api schema
        if request.path == '/api_schema':
            return True
        # Authenticate
        user = request.user
        if not user.is_authenticated:
            return False

        print(f"--- Test Permission ---")

        object_pk = view.kwargs.get('pk', None)

        # Return True (not required perm) when object with PK doesn't required perm PK
        if object_pk is not None:
            return True

        # Get full required permission (with action and PK), perm_name (without action and PK)
        required_permission, perm_name = get_required_permission(self, view, request)

        # If function not required any permission, return True
        is_perm = perm_exist(required_permission)
        if not is_perm:
            return True

        # Get the action from required permission
        action = required_permission.split('_')[0]

        user_group_perm = user.is_group_has_perm(required_permission)
        user_perm = user.is_perm(required_permission)
        if action == "create" and 'pk' not in view.kwargs:
            return user_group_perm or user_perm

        has_perm = user_has_perm(user, required_permission)
        print(f"Check permission time: {time.time() - start_time}")
        # If user or nhom user has perm, return True
        return has_perm

    def has_object_permission(self, request, view, obj):
        print(f"SUPER TESTING FROM HERE")
        start_time = time.time()
        # Authenticate
        user = request.user
        if not user.is_authenticated:
            return False
        object_pk = view.kwargs.get('pk', None)
        required_permission, perm_name = get_required_permission(self, view, request)
        # Add PK to string perm
        required_permission = f"{required_permission}_{object_pk}"
        # Checking perm with PK is exist
        perm = perm_exist(required_permission)
        # If perm PK exist, handling validate perm user
        if perm is not None:
            # Check if user or user_nhom has perm PK
            user_perm = user.is_allow(required_permission)
            user_nhom_perm = user.is_group_has_perm(required_permission)
            # If user or nhom user has perm, return True
            return user_nhom_perm or user_perm
        print(f"Check objects permission time: {time.time() - start_time}")
        # Check if user has the permission
        return True


def get_required_permission(self, view, request):
    # Get module_name
    modules = view.__module__.split('.')
    contents_type = ContentType.objects.values_list('app_label', flat=True).distinct()
    module_name = ''
    for module in modules:
        if module in contents_type:
            module_name = module
            break
    # Get action of function
    try:
        action = view.action
    except AttributeError:
        action = {
            'GET': 'retrieve' if 'pk' in view.kwargs else 'list',
            'POST': 'create',
            'PUT': 'update',
            'PATCH': 'partial_update',
            'DELETE': 'destroy'
        }.get(request.method, 'read')
    action = 'list' if action == 'now' else action
    content_type = ContentType.objects.get_for_model(self.model)
    # Merge string from above data to generated permission name
    return f'{action}_{module_name}_{content_type.model}', f'{module_name}_{content_type.model}'
