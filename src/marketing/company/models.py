from django.db import models


# Create your models here.
class Company(models.Model):
    id = models.CharField(primary_key=True, max_length=6, unique=True)
    name = models.CharField(max_length=255)
    note = models.TextField(null=True, blank=True)
    color_code = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
