from django.contrib import admin
from account.models import User, UserPerm, UserGroupPerm, Perm, GroupPerm


class NhomQuyenUserInline(admin.TabularInline):  # Hoặc StackedInline
    model = UserGroupPerm


class QuyenUserInline(admin.TabularInline):  # Hoặc StackedInline
    model = UserPerm


class UserAdmin(admin.ModelAdmin):
    inlines = [NhomQuyenUserInline, QuyenUserInline]
    search_fields = ("id", "username", "email", "phone_number")

    def get_fieldsets(self, request, obj=None):
        """Override the fieldsets to exclude group and permission fields."""
        fieldsets = super().get_fieldsets(request, obj=obj)
        # Remove 'groups' and 'user_permissions' from the fieldsets
        fieldsets = list(fieldsets)
        fieldsets[0] = (
        None, {'fields': ['id', 'username', 'email', 'phone_number', 'password', 'region', 'status', 'user_type', 'is_active', 'is_staff', 'is_superuser', 'last_login']})
        return tuple(fieldsets)


# Register your models here.
admin.site.register(User, UserAdmin)
admin.site.register(GroupPerm)
admin.site.register(Perm)
