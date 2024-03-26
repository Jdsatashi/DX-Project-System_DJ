from django.db import models

from account.models import User


# Create your models here.
class NVPhongBan(models.Model):
    maPhongBan = models.CharField(max_length=50, primary_key=True, unique=True)
    tenPhongBan = models.CharField(max_length=255, null=False, blank=False)
    moTa = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'nv_phongban'

    def __str__(self):
        return f"Phòng ban: {self.tenPhongBan}"


class NVChucDanh(models.Model):
    maChucDanh = models.CharField(max_length=50, primary_key=True, unique=True)
    tenChucDanh = models.CharField(max_length=255, null=False, blank=False)
    moTa = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'nv_chucdanh'

    def __str__(self):
        return f"Chức danh: {self.tenChucDanh}"


class NVProfile(models.Model):
    maNV = models.ForeignKey(User, to_field='id', null=False, on_delete=models.CASCADE)
    maPhongBan = models.ForeignKey(NVPhongBan, to_field='maPhongBan', null=True, blank=False, on_delete=models.SET_NULL)
    maChucDanh = models.ForeignKey(NVChucDanh, to_field='maChucDanh', null=True, blank=False, on_delete=models.SET_NULL)
    fullname = models.CharField(max_length=255)
    gioiTinh = models.CharField(max_length=1)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'nv_profile'
