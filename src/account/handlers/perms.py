from django.contrib.contenttypes.models import ContentType
from django.db import models


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
