from django.db import models

from account.models import User


# Create your models here.
class Order(models.Model):
    id = models.CharField(max_length=24)
    date_get = models.DateField()
    date_dx_received = models.DateTimeField()
    client_id = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    date_lv1_send = models.DateTimeField(null=True)
    date_delay = models.IntegerField(default=0)

    created_by = models.CharField(max_length=64)
    note = models.CharField(max_length=255, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
