from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.db import models

from account.models import Perm


class GetPerm:
    def __init__(self, model):
        if not model or not issubclass(model, models.Model):
            raise ImproperlyConfigured("A valid Django model must be provided")
        self.model = model

    def perm_name(self):
        c = ContentType.objects.get_for_model(self.model)
        return f"{c.app_label}_{c.model}"

    def perm_action(self, action):
        if action:
            perm_name = self.perm_name()
            return f"{action}_{perm_name}"
        raise ValueError({"message": "Action is not provided"})

    def perm_pk(self, pk):
        if pk:
            perm_name = self.perm_name()
            return f"{perm_name}_{pk}"
        raise ValueError({"message": "PK is not provided"})

    def perm_full(self, action, pk):
        if action and pk:
            perm_name = self.perm_name()
            return f"{action}_{perm_name}_{pk}"
        raise ValueError({"message": "Action and PK are not provided"})
