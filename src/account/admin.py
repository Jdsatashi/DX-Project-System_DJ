from django.contrib import admin
from account.models import User, UserAdmin # NhomUser, QuyenHanUser

# Register your models here.
admin.site.register(User, UserAdmin)
