from django.contrib import admin
from user_system.nv_profile.models import NVChucDanh, NVPhongBan, NVProfile


# Register your models here.
admin.site.register(NVChucDanh)
admin.site.register(NVPhongBan)
admin.site.register(NVProfile)
