# models.py
import datetime

from django.apps import apps
from django.contrib.auth.hashers import is_password_usable, make_password
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone
from pyodbc import IntegrityError

from app.logs import app_log
from utils.constants import maNhomND
from utils.helpers import self_id


# Custom command create_user or create_super user
class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, phone_number, password=None, **extra_fields):
        user = self.model(
            username=username,
            email=self.normalize_email(email),
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        for number in phone_number:
            PhoneNumber.objects.create(user=user, phone_number=number)
        return user

    def create_superuser(self, username, email, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        username = username if username and username != '' else extra_fields.get('id')
        type_nv = "employee"
        extra_fields['user_type'] = type_nv
        user = self.create_user(username, email, phone_number, password, **extra_fields)
        perms = Perm.objects.all()
        for i, q in enumerate(perms):
            user.perm_user.add(q)
        return user


# Self define user model attributes
class User(AbstractBaseUser, PermissionsMixin):
    id = models.CharField(primary_key=True, unique=True, null=False)
    username = models.CharField(max_length=255, unique=True, null=True, blank=True, default=None)
    email = models.EmailField(unique=False, null=True, blank=True, default=None)
    password = models.CharField(max_length=512, null=False)
    region = models.CharField(max_length=100, null=True, blank=True, default=None)
    status = models.CharField(max_length=40, null=True, default=None)
    user_type = models.CharField(max_length=24, default='client', choices=(
        ('employee', 'employee'), ('client', 'client'), ('farmer', 'farmer')))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    group_user = models.ManyToManyField('GroupPerm', through='UserGroupPerm', blank=True, related_name='users_rela')
    perm_user = models.ManyToManyField('Perm', through='UserPerm', blank=True, related_name='users_rela')

    device_token = models.CharField(max_length=255, null=True)

    # System auth django attribute
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True, default=None)

    objects = CustomUserManager()

    # Required fields for create account command
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['id', 'email']

    # define table name
    class Meta:
        db_table = 'users'

    # Return data user object
    def __str__(self):
        return f"{self.id}"

    def save(self, *args, **kwargs):
        self.id = self.id.upper()
        if not self.id or self.id == '':
            char = 'NV' if self.user_type == 'employee' else 'KH'
            self.id = self_id(char, User, 4)
        self.username = self.username if self.username and self.username != '' else self.id
        if self.password is None or self.password == '':
            self.password = self.id.lower()

        if not is_password_usable(self.password):
            self.password = make_password(self.password)

        if self.email == '':
            self.email = None
        self.clean()
        super().save(*args, **kwargs)
        if self.user_type == 'employee':
            EmployeeProfile = apps.get_model('employee_profile', 'EmployeeProfile')
            profile = EmployeeProfile.objects.filter(employee_id=self).first()
            if not profile:
                EmployeeProfile.objects.create(employee_id=self)
        else:
            ClientProfile = apps.get_model('client_profile', 'ClientProfile')
            ClientGroup = apps.get_model('client_group', 'ClientGroup')
            farmer_group = ClientGroup.objects.filter(id=maNhomND).first()
            app_log.info(f"testing: {farmer_group}")
            profile = ClientProfile.objects.filter(client_id=self).first()
            if not profile:
                ClientProfile.objects.create(client_id=self, client_group_id=farmer_group, register_name=f"Nông dân {self.id}")

    def is_perm(self, permission):
        return self.perm_user.filter(name=permission).exists()

    def is_allow(self, permission):
        is_perm = self.is_perm(permission)
        if is_perm:
            perm = self.perm_user.filter(name=permission).first()
            user_perm = UserPerm.objects.get(user=self, perm=perm)
            return user_perm.allow
        return is_perm

    def is_group_has_perm(self, permission):
        group_user = self.group_user.all()
        valid = False
        for group in group_user:
            valid = group.group_has_perm(permission)
            if valid:
                break
        return valid

    def get_all_allow_perms(self):
        user_perms = set(self.perm_user.filter(userperm__allow=True).values_list('name', flat=True))

        group_perms = set()
        for group in self.group_user.all():
            group_perms.update(
                group.perm.filter(groupperm__allow=True, groupperm__usergroupperm__allow=True).values_list('name',
                                                                                                           flat=True))

        return user_perms.union(group_perms)


class PhoneNumber(models.Model):
    phone_number = models.CharField(max_length=24, primary_key=True)
    user = models.ForeignKey(User, related_name='phone_numbers', null=True, on_delete=models.CASCADE)


# Table for save Token
class RefreshToken(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    phone_number = models.ForeignKey(PhoneNumber, null=True, on_delete=models.CASCADE)
    refresh_token = models.TextField(null=True)
    status = models.CharField(max_length=128, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.status == "active":
            now = timezone.now()
            time_threshold = now - datetime.timedelta(hours=24)
            # RefreshToken.objects.filter(
            #     user=self.user,
            #     status="expired",
            #     updated_at__lt=time_threshold
            # ).exclude(
            #     id=self.id
            # ).delete()
            # app_log.info(f"Model set expired")
            # RefreshToken.objects.filter(
            #     user=self.user,
            # ).exclude(
            #     id=self.id
            # ).update(status="expired")

        super().save(*args, **kwargs)


class TokenMapping(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    refresh_jti = models.CharField(max_length=255)
    access_jti = models.CharField(max_length=255)
    expired_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        refresh_id = TokenMapping.objects.filter(refresh_jti=self.refresh_jti)
        if refresh_id.exists():
            refresh_id.exclude(access_jti=self.access_jti).delete()
        super().save(*args, **kwargs)


class Verify(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verify')
    phone_verify = models.ForeignKey(PhoneNumber, max_length=24, null=True, related_name='phone_numbers',
                                     on_delete=models.CASCADE)
    refresh_token = models.ForeignKey(RefreshToken, null=True, on_delete=models.CASCADE)
    is_verify = models.BooleanField(default=False)
    verify_code = models.CharField(max_length=64)
    verify_type = models.CharField(max_length=128, default=None)
    device_code = models.CharField(max_length=255, null=True)
    note = models.TextField(null=True, default=None)
    verify_time = models.DateTimeField(null=True)
    expired_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users_verify'
        get_latest_by = 'created_at'

    def save(self, *args, **kwargs):
        if not self.id:
            self.expired_at = timezone.now() + datetime.timedelta(seconds=1800)
        super(Verify, self).save(*args, **kwargs)

    def get_new_code(self, otp_code, *args, **kwargs):
        self.verify_code = otp_code
        self.expired_at = timezone.now() + datetime.timedelta(seconds=1800)
        self.save()

    def is_verify_valid(self):
        now = timezone.now()
        return self.created_at <= now <= self.expired_at


# Perm as known as Permissions
class Perm(models.Model):
    name = models.CharField(max_length=255, primary_key=True)
    note = models.TextField(null=True, default=None, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    content_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=255)
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        db_table = 'users_perm'

    def __str__(self):
        return f"{self.name}"


# GroupPerm as a Permissions Group or Roles User
class GroupPerm(models.Model):
    name = models.CharField(max_length=255, primary_key=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    parent_group = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    note = models.TextField(null=True, default=None, blank=True)
    perm = models.ManyToManyField(to='Perm', through='GroupPermPerms', blank=True)
    # perm = models.ManyToManyField(Perm, blank=True)
    allow = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users_group_perm'

    def group_has_perm(self, permission):
        perm = self.perm.filter(name=permission)
        return perm.exists() and self.allow


# Table/Model middleman of Perm and User
class UserPerm(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    perm = models.ForeignKey(Perm, on_delete=models.CASCADE)
    allow = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if UserPerm.objects.filter(user=self.user, perm=self.perm).exists():
            raise IntegrityError

    class Meta:
        db_table = 'users_user_perm'

    def __str__(self):
        return f"{self.user} - {self.perm}"


# Table/Model middleman of Group and User
class UserGroupPerm(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(GroupPerm, on_delete=models.CASCADE)
    allow = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users_user_group_perm'


class GroupPermPerms(models.Model):
    perm = models.ForeignKey(Perm, on_delete=models.CASCADE, related_name='perm_group')
    group = models.ForeignKey(GroupPerm, on_delete=models.CASCADE, related_name='perm_group')
    allow = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users_groupperm_perm'

"""
RefreshToken.objects.filter(
    phone_number=self.phone_number,
    status="active"
).exclude(
    id=self.id
).update(status="expired")
RefreshToken.objects.filter(
    user=self.user,
    status="active"
).exclude(
    id=self.id
).update(status="deactivate")
"""
