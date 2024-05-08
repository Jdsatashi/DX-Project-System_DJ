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
        print(f"--- Test Permission ---")
        object_pk = view.kwargs.get('pk', None)
        if object_pk is not None:
            # Return True (not required perm) when object with PK doesn't required perm PK
            return True

        required_permission, perm_name = get_required_permission(self, view, request)

        is_perm = perm_exist({'name': required_permission})
        if not is_perm:
            return True
        # Check if user or user_nhom has perm
        user_nhom_perm = user.is_group_has_perm(required_permission)
        user_perm = user.is_perm(required_permission)

        # Check if user
        has_obj_perm = user.perm_user.filter(name__icontains=required_permission).exists()

        obj_group = user.group_user.filter(perm__name__icontains=required_permission).first()
        has_obj_group = obj_group.perm.filter(name__icontains=required_permission).exists()
        print(obj_group.perm.filter(name__icontains=required_permission).first())
        if has_obj_perm:
            return has_obj_perm
        # Check if object has PK

        # If user or nhom user has perm, return True
        return user_nhom_perm or user_perm or has_obj_perm or has_obj_group

    def has_object_permission(self, request, view, obj):
        print(f"SUPER TESTING FROM HERE")
        # Authenticate
        user = request.user
        if not user.is_authenticated:
            return False
        object_pk = view.kwargs.get('pk', None)
        required_permission, perm_name = get_required_permission(self, view, request)
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
        # Check if user has the permission
        return True


# Check if permission exist
def perm_exist(perm: dict):
    # Validate perm is dictionary and perm has value
    if not isinstance(perm, dict) or perm is None:
        raise ValueError("perm must be a dictionary {'key': value}.")

    q = Perm.objects.filter(name=perm.get('name'))
    return q.first() if q.exists() else None


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
    content_type = ContentType.objects.get_for_model(self.model)
    # Merge string from above data to generated permission name
    return f'{action}_{module_name}_{content_type.model}', f'{module_name}_{content_type.model}'
