from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response

from account.models import Perm, User
from app.logs import app_log
from utils.constants import perm_actions


def get_action(view, method):
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
        }.get(method, 'list')
    return action


def get_perm_name(model):
    content_type = ContentType.objects.get_for_model(model)
    return f"{content_type.app_label}_{content_type.model}"


def get_required_permission(model, view, request):
    action = get_action(view, request.method)
    perm_name = get_perm_name(model)
    return f"{action}_{perm_name}"


class DataFKModel:
    def __init__(self, model):
        self.model = model

    def get_fk_fields(self):
        """
        Get all ForeignKey fields of model
        """
        foreign_keys = []
        for field in self.model._meta.get_fields():
            if isinstance(field, (models.ForeignKey, models.OneToOneField)):
                foreign_keys.append(field.name)
        return foreign_keys

    def get_fk_models(self):
        """
        Get all ForeignKey models
        """
        foreign_keys = []
        for field in self.model._meta.get_fields():
            if isinstance(field, (models.ForeignKey, models.OneToOneField)):
                foreign_keys.append(field)
        return foreign_keys

    def get_fk_fields_models(self):
        """
        Get all ForeignKey fields of model
        """
        foreign_keys = []
        for field in self.model._meta.get_fields():
            if isinstance(field, (models.ForeignKey, models.OneToOneField)):
                data = {'field': field.name, 'model': field.related_model}
                foreign_keys.append(data)
        return foreign_keys


def perm_queryset(self):
    user = self.request.user
    model_class = self.serializer_class.Meta.model
    pk = self.kwargs.get('pk')
    if user.is_superuser:
        return model_class.objects.all()
    if not user.is_authenticated:
        return Response({'message': 'User is not authenticate'}, status=status.HTTP_401_UNAUTHORIZED)
    if not self.permission_classes:
        return model_class.objects.all()
    all_permissions = user.get_all_allow_perms()
    has_perm_id = []

    content = ContentType.objects.get_for_model(model_class)
    action_perm = perm_actions.get('view')
    perm_name = f'{content.app_label}_{content.model}'
    if pk:
        perm_name = f'{perm_name}_{pk}'
    # Get all price list ids which required permissions
    perms_content = Perm.objects.filter(name__icontains=perm_name)
    perm_req_id = {v.object_id for v in perms_content if v.object_id}

    # Get all price list ids which user has permissions
    for perm in all_permissions:
        if perm.startswith(action_perm + '_' + perm_name):
            _, object_id = perm.rsplit('_', 1)
            has_perm_id.append(object_id)
    app_log.info(f"Require perm: {perm_req_id}")
    app_log.info(f"User has perm: {has_perm_id}")
    # Exclude item which use not has permission
    exclude_id = list(perm_req_id - set(has_perm_id))
    app_log.info(f"Query exclude: {exclude_id}")
    return model_class.objects.exclude(id__in=exclude_id)


def get_full_permname(model, action, pk):
    perm_name = get_perm_name(model)
    if pk:
        perm_name = f'{perm_name}_{pk}'
    return f'{action}_{perm_name}'


def get_user_by_permname(perm_name):
    user_group = User.objects.filter(
        Q(group_user__perm__name=perm_name, group_user__usergroupperm__allow=True) |
        Q(perm_user__name=perm_name, perm_user__userperm__allow=True)
    ).distinct().values_list('id', flat=True)
    return list(user_group)
