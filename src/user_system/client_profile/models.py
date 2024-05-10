from django.db import models

from account.models import User
from user_system.client_group.models import ClientGroup


# Create your models here.
class ClientProfile(models.Model):
    client_id = models.OneToOneField(User, to_field='id', on_delete=models.CASCADE)
    register_name = models.CharField(max_length=255, null=False)
    organization = models.CharField(max_length=255, null=True)
    dob = models.DateField(null=True)
    client_group_id = models.ForeignKey(ClientGroup, on_delete=models.CASCADE)
    nvtt_id = models.CharField(max_length=255, null=True)
    address = models.TextField(null=True)
    client_lv1_id = models.CharField(max_length=255, null=True)
    created_by = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clients_profile'
