from functools import wraps

from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render
from rest_framework import permissions

from account.models import Perm


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
        # Allow showing on api schema
        if request.path == '/api_schema':
            return True
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
        print(f"--- Test Permission ---")
        print(view)
        print(request.method)
        object_pk = view.kwargs.get('pk', None)
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
        content_type = ContentType.objects.get_for_model(self.model)
        # Merge string from above data to generated permission name
        required_permission = f'{action}_{module_name}_{content_type.model}'
        is_perm = perm_exist({'name': required_permission})
        if not is_perm:
            print(f"Permission no exists")
            return True
        # Check if user or user_nhom has perm
        user_nhom_perm = user.is_group_has_perm(required_permission)
        user_perm = user.is_perm(required_permission)
        has_obj_perm = user.perm_user.filter(name__icontains=required_permission).exists()
        if has_obj_perm:
            return has_obj_perm
        # Check if object has PK
        if object_pk is not None:
            print(f"PK is not None")
            # Add PK to string perm
            required_permission = f"{required_permission}_{object_pk}"
            # Checking perm with PK is exist
            perm = perm_exist({'name': required_permission})
            # If perm PK exist, handling validate perm user
            if perm is not None:
                # Check if user or user_nhom has perm PK
                user_perm = user.is_allow(required_permission)
                user_nhom_perm = user.is_group_has_perm(required_permission)
                # If user or nhom user has perm, return True
                return user_nhom_perm or user_perm
            # Return True (not required perm) when object with PK doesn't required perm PK
            return True
        # If user or nhom user has perm, return True
        return user_nhom_perm or user_perm

    def has_object_permission(self, request, view, obj):
        # Superusers have full access
        if request.user.is_superuser:
            return True

        # Determine the action
        if hasattr(view, 'action'):
            action = view.action
        else:
            action = {
                'GET': 'retrieve' if 'pk' in view.kwargs else 'list',
                'POST': 'create',
                'PUT': 'update',
                'PATCH': 'partial_update',
                'DELETE': 'destroy'
            }.get(request.method, '')

        # Build the permission string
        content_type = ContentType.objects.get_for_model(obj)
        required_permission = f"{action}_{content_type.app_label}_{content_type.model}_{obj.id}"

        # Check if user has the permission
        return request.user.is_perm(required_permission)


# Check if permission exist
def perm_exist(perm: dict):
    # Validate perm is dictionary and perm has value
    if not isinstance(perm, dict) or perm is None:
        raise ValueError("perm must be a dictionary {'key': value}.")

    q = Perm.objects.filter(name=perm.get('name'))
    return q.first() if q.exists() else None
