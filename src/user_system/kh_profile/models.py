from django.db import models

from account.models import User
from user_system.kh_nhomkh.models import NhomKH


# Create your models here.
class KHProfile(models.Model):
    maKH = models.ForeignKey(User, to_field='id', on_delete=models.CASCADE)
    tenBanKe = models.CharField(max_length=255, null=False)
    tenDoanhNghiep = models.CharField(max_length=255, null=True)
    maNhomKH = models.ForeignKey(NhomKH, on_delete=models.CASCADE)
    maNVTT = models.CharField(max_length=255, null=True)
    diaChi = models.TextField(null=True)
    nguoiLap = models.TextField(null=True)
    maKHCap1 = models.CharField(max_length=255, null=True)

    class Meta:
        db_table = 'kh_profile'
