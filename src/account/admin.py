from django.contrib import admin
from account.models import User, NhomUser, QuyenHanUser

# Register your models here.
admin.site.register(User)
admin.site.register(NhomUser)
admin.site.register(QuyenHanUser)
