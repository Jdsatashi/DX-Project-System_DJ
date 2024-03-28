from django.contrib import admin
from account.models import User, NhomUser, QuyenHanUser, UserAdmin

# Register your models here.
admin.site.register(User, UserAdmin)
admin.site.register(NhomUser)
admin.site.register(QuyenHanUser)
