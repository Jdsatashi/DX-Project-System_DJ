from django.db import models

from account.models import User


# Create your models here.
class NhomKH(models.Model):
    maNhom = models.CharField(max_length=50, unique=True, primary_key=True)
    maNhomCha = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    tenNhom = models.CharField(max_length=255)
    moTa = models.TextField(null=True)
    nguoiLap = models.ForeignKey(User, to_field='usercode', on_delete=models.SET_NULL)
    timestamp = models.DateTimeField(auto_now_add=True)
