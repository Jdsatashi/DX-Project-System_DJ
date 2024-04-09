from django.contrib import admin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, ReadOnlyPasswordHashField
from django.contrib.auth.hashers import make_password
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django import forms

from account.models import User, UserPerm, UserGroupPerm, Perm, GroupPerm


class NhomQuyenUserInline(admin.TabularInline):
    model = UserGroupPerm


class QuyenUserInline(admin.TabularInline):
    model = UserPerm


class UserAdmin(BaseUserAdmin):
    inlines = [NhomQuyenUserInline, QuyenUserInline]
    search_fields = ("id", "username", "email", "phone_number")
    list_display = ('id', 'username', 'email', 'phone_number')

    def get_fieldsets(self, request, obj=None):
        """Override the fieldsets to exclude group and permission fields."""
        # fieldsets = super().get_fieldsets(request, obj=obj)
        # # Remove 'groups' and 'user_permissions' from the fieldsets
        # fieldsets = list(fieldsets)
        # fieldsets[0] = (None, {'classes': ('wide',), 'fields': (
        #     'id', 'username', 'email', 'phone_number', 'password1', 'password2', 'region', 'status', 'user_type')})
        if obj is None:  # Adding a new user
            return (
                (None, {'classes': ('wide',), 'fields': (
                    'id', 'username', 'email', 'phone_number', 'password1', 'password2', 'region', 'status',
                    'user_type')}),
            )
        else:  # Editing an existing user
            return (
                (None, {'classes': ('wide',), 'fields': (
                    'username', 'email', 'phone_number', 'region', 'status', 'user_type', 'is_active', 'is_staff',
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
