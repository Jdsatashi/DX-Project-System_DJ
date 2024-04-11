from django.db import models


# Create your models here.
class Status(models.Model):
    name = models.CharField(primary_key=True, max_length=32)
    note = models.TextField(null=True, blank=True)
