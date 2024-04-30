# models.py
import datetime

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from user_system.user_type.models import UserType


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
        type_nv, _ = UserType.objects.get_or_create(user_type="employee")
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
    user_type = models.ForeignKey(UserType, to_field='user_type', null=True, blank=False, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    group_user = models.ManyToManyField('GroupPerm', through='UserGroupPerm', blank=True, related_name='users_rela')
    perm_user = models.ManyToManyField('Perm', through='UserPerm', blank=True, related_name='users_rela')

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
        self.username = self.username if self.username and self.username != '' else self.id
        # if self.password is None or self.password == '':
        #     self.password = make_password(self.id.lower())
        self.clean()
        super().save(*args, **kwargs)

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


class PhoneNumber(models.Model):
    phone_number = models.CharField(max_length=24, primary_key=True)
    user = models.ForeignKey(User, related_name='phone_numbers', null=True, on_delete=models.CASCADE)


class Verify(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verify')
    phone_verify = models.ForeignKey(PhoneNumber, max_length=24, null=True, related_name='phone_numbers',
                                     on_delete=models.CASCADE)
    refresh_token = models.CharField(max_length=255, null=True)
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

    def save(self, *args, **kwargs):
        if not self.id:
            self.expired_at = timezone.now() + datetime.timedelta(seconds=1800)
        super(Verify, self).save(*args, **kwargs)

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


# GroupPerm as a Permissions Group or Roles User
class GroupPerm(models.Model):
    name = models.CharField(max_length=255, primary_key=True)
    note = models.TextField(null=True, default=None, blank=True)
    perm = models.ManyToManyField(Perm, blank=True)
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
