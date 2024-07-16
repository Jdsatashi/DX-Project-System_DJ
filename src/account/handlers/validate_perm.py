import time
from functools import wraps

from django.shortcuts import render
from rest_framework import permissions

from account.handlers.perms import get_perm_name, get_action, get_required_permission, DataFKModel
from account.models import UserPerm
from app.logs import app_log
from utils.constants import perm_actions
from utils.perms.check import perm_exist


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
    message = {'message': ''}

    def __init__(self, model, user=None):
        super().__init__()
        self.model = model
        self.user = user

    def has_permission(self, request, view):
        start_time = time.time()
        # Pop errors in message
        msg_err = self.message.get('errors')
        if msg_err:
            self.message.pop('errors')
        # Allow showing on api schema
        if request.path == '/api_schema':
            return True
        # Authenticate defaults user
        user = request.user
        if not user.is_authenticated:
            self.message['message'] = 'Bạn chưa đăng nhập.'
            return False
        user = user if self.user is None else self.user

        object_pk = view.kwargs.get('pk', None)
        # Return True (not required perm) when object with PK doesn't required perm PK
        if object_pk is not None:
            return True
        action = get_action(view, request.method)

        app_log.info(f"--- Test Permission ---")
        perm_name = get_perm_name(self.model)
        # Check all perm
        all_perm = perm_actions['all'] + f"_{perm_name}"
        if user.is_group_has_perm(all_perm) or user.is_perm(all_perm):
            return True

        # Get full required permission (with action and PK), perm_name (without action and PK)
        required_permission = f"{action}_{perm_name}"
        # If function not required any permission, return True
        is_perm = perm_exist(required_permission)
        if not is_perm:
            return True

        # if action == "create" and 'pk' not in view.kwargs:
        if action == perm_actions['view']:
            return True

        result, messages = self.validate_fk_perm(request, action, user)
        for message in messages:
            self.message['errors'] = {message['field']: message['value']}

        # Set valid if user is allowed
        print(f"{required_permission}")
        user_has_perm = user.is_perm(required_permission)
        if user_has_perm:
            if not user.is_allow(required_permission):
                return False
        # Get user groups has permission
        is_valid = user.is_group_allow(required_permission)
        print(f"Test valid: {is_valid}")
        app_log.info(f"Check permission time: {time.time() - start_time}")
        if not result or not is_valid:
            message = f"bạn không đủ quyền để thực hiện {action} {perm_name}"
            self.message['message'] = message
        # If user or nhom user has perm, return True
        return result and is_valid

    def has_object_permission(self, request, view, obj):
        start_time = time.time()
        # Authenticate
        user = request.user
        if not user.is_authenticated:
            return False
        object_pk = view.kwargs.get('pk', None)
        required_permission = get_required_permission(self.model, view, request)
        # Add PK to string perm
        required_permission = f"{required_permission}_{object_pk}"
        app_log.info(f"Test reequired permission {required_permission}")
        # Checking perm with PK is exist
        perm = perm_exist(required_permission)
        app_log.info(f"Check perm exist time: {time.time() - start_time}")
        # If perm PK exist, handling validate perm user
        if perm is not None:
            # Check if user or user_nhom has perm PK
            user_perm = user.is_allow(required_permission)
            user_nhom_perm = user.is_group_has_perm(required_permission)
            # If user or nhom user has perm, return True
            return user_nhom_perm or user_perm
        app_log.info(f"Check objects permission time: {time.time() - start_time}")
        # Check if user has the permission
        return True

    def validate_fk_perm(self, request, action, user):
        """ Check relation of model with ForeignKey and its perms"""
        start_time = time.time()
        print(f"Check user: {user.id}")
        # Get list of ForeignKey fields
        fk_model = DataFKModel(self.model)
        list_fk = fk_model.get_fk_fields_models()
        # Create perm_pk store perm and value
        perm_pk = dict()
        messages = []
        # Loop on list FK
        for fk_fields in list_fk:
            # print(f"TEST FK Field: {fk_fields}")
            # print(f"TEST FK Requires Permission: {required_permission}")
            # Create key - value with fields is key and value is dict
            field_name = fk_fields['field']
            perm_pk[field_name] = dict()
            # Get value of FK from request data
            fk_value = request.data.get(field_name, None)
            # Set value to perm_pk[field]
            perm_pk[field_name]['value'] = fk_value
            # Check value
            if fk_value is None:
                app_log.info(f"FK is None, perm is True")
                perm_pk[field_name]['is_perm'] = True
                continue

            # Get perm_name from FK model
            perm_name = get_perm_name(fk_fields['model'])
            # Concat action with perm_name and fk_value as id
            required_permission = f"{action}_{perm_name}_{fk_value}"
            # Validate is require permission exist
            if not perm_exist(required_permission):
                # If not exist, set perm to True
                print(f"FK {field_name} perm not exist: {required_permission}")
                perm_pk[field_name]['is_perm'] = True
                continue

            # Validate user has perm
            if user.is_allow(required_permission):
                print(f"User has perm {required_permission}")
                # If user has perm, set perm to True
                perm_pk[field_name]['is_perm'] = True
            # Validate user group has perm
            elif user.is_group_allow(required_permission):
                print(f"User group has perm {required_permission}")
                # If user group has perm, set perm to True
                perm_pk[field_name]['is_perm'] = True
            else:
                print(f"Error: {field_name}")
                perm_pk[field_name]['is_perm'] = False
                messages.append({
                    'field': field_name,
                    'value': fk_value
                })

        result = all(result['is_perm'] for result in perm_pk.values())

        app_log.info(f"Perm result: {result}")
        app_log.info(f"Time validate FK: {time.time() - start_time}")
        return result, messages


def check_perm(user, permission: str, perm_name: str):
    all_perm = perm_actions['all'] + f"_{perm_name}"
    print(f"Check perm: {all_perm}")
    if user.is_group_has_perm(all_perm) or user.is_perm(all_perm):
        return True

    is_perm = perm_exist(permission)
    if not is_perm:
        return True

    user_has_perm = user.is_perm(permission)
    if user_has_perm:
        if not user.is_allow(permission):
            return False
    # Get user groups has permission
    is_valid = user.is_group_allow(permission)
    return is_valid
