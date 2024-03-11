from django.db import models


# model
class KhachHangModel(models.Model):
    maKhachHang = models.CharField(max_length=150, primary_key=True)
    tenBanKe = models.CharField(max_length=250, null=True)
    tenDoanhNghiep = models.CharField(max_length=250, null=True)
    maNhomKH = models.CharField(max_length=50, null=True)
    maNhanVienTT = models.CharField(max_length=250, null=True)
    dienThoai = models.CharField(max_length=250, null=True)
    email = models.CharField(max_length=250, null=True)
    diaChi = models.CharField(max_length=350, null=True)
    ngayLap = models.DateTimeField(null=True)
    nguoiLap = models.CharField(max_length=50, null=True)
    matKhau = models.CharField(max_length=250, null=True)
    maKhachHangCap1 = models.CharField(max_length=50, null=True)

    class Meta:
        # Name table in the database
        db_table = 'tbl_QLTT_KhachHang'
        # Not manage table structure
        managed = False
