from django.db import models

from account.models import User


# Create your models here.
class NVPhongBan(models.Model):
    maPhongBan = models.CharField(max_length=50, primary_key=True, unique=True)
    tenPhongBan = models.CharField(max_length=255, unique=True)
    moTa = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)


class NVChucDanh(models.Model):
    maChucDanh = models.CharField(max_length=50, primary_key=True, unique=True)
    tenChucDanh = models.CharField(max_length=255, unique=True)
    moTa = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)


class NVProfile(models.Model):
    maNV = models.ForeignKey(User, to_field='usercode', null=False, on_delete=models.SET_NULL)
    maPhongBan = models.ForeignKey(NVPhongBan, to_field='maPhongBan', null=False, blank=False, on_delete=models.SET_NULL)
    maChucDanh = models.ForeignKey(NVChucDanh, to_field='maChucDanh', null=False, blank=False, on_delete=models.SET_NULL)
    fullname = models.CharField(max_length=255)
    gioiTinh = models.CharField(max_length=1)
    timestamp = models.DateTimeField(auto_now_add=True)
