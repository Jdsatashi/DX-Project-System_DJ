from django.db import models

from account.models import User


# Create your models here.
class ClientGroup(models.Model):
    id = models.CharField(max_length=50, unique=True, primary_key=True)
    parent_id = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    note = models.TextField(null=True, blank=True)
    created_by = models.CharField(max_length=255, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'client_group'

    def __str__(self):
        return f"{self.id} - {self.name}"
