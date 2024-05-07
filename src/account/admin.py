from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.hashers import make_password

from account.models import User, UserPerm, UserGroupPerm, Perm, GroupPerm, PhoneNumber


class NhomQuyenUserInline(admin.TabularInline):
    model = UserGroupPerm


class QuyenUserInline(admin.TabularInline):
    model = UserPerm


class UserAdmin(BaseUserAdmin):
    inlines = [NhomQuyenUserInline, QuyenUserInline]
    search_fields = ("id", "username", "email", "phone_numbers__phone_number")
    list_display = ('id', 'username', 'email', 'display_phone_numbers')

    def display_phone_numbers(self, obj):
        return ", ".join([phone_number.phone_number for phone_number in obj.phone_numbers.all()])
    display_phone_numbers.short_description = 'Phone Numbers'

    def get_fieldsets(self, request, obj=None):
        """Override the fieldsets to exclude group and permission fields."""
        if obj is None:  # Adding a new user
            return (
                (None, {'classes': ('wide',), 'fields': (
                    'id', 'username', 'email', 'password1', 'password2', 'region', 'status',
                    'user_type')}),
            )
        else:  # Editing an existing user
            return (
                (None, {'classes': ('wide',), 'fields': (
                    'username', 'email', 'region', 'status', 'user_type', 'is_active', 'is_staff',
                    'is_superuser')}),
            )

    def save_model(self, request, obj, form, change):
        if 'password' in form.changed_data:
            obj.password = make_password(obj.password)
        super().save_model(request, obj, form, change)


# Register your models here.
admin.site.register(User, UserAdmin)
admin.site.register(GroupPerm)
admin.site.register(Perm)
admin.site.register(PhoneNumber)
