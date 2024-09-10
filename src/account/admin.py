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
                    'username', 'email', 'password1', 'password2', 'region', 'status', 'user_type', 'is_active', 'is_staff',
                    'is_superuser')}),
            )

    def save_model(self, request, obj, form, change):
        if 'password' in form.changed_data:
            obj.password = make_password(obj.password)
        super().save_model(request, obj, form, change)


class GroupPermAdmin(admin.ModelAdmin):
    search_fields = (
        "name", "display_name", "description", "users_rela__username", "users_rela__id", "users_rela__email")


class PermAdmin(admin.ModelAdmin):
    search_fields = (
        "name", "display_name", "description", "users_rela__username", "users_rela__id", "users_rela__email")


class PhoneNumberAdmin(admin.ModelAdmin):
    search_fields = (
        "phone_number", "user__username", "user__email")  # Adjust this according to the fields you want to search


# Register your models here.
admin.site.register(User, UserAdmin)
admin.site.register(GroupPerm, GroupPermAdmin)
admin.site.register(Perm, PermAdmin)
admin.site.register(PhoneNumber, PhoneNumberAdmin)
