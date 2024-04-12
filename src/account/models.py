# models.py
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from user_system.user_type.models import UserType


# Custom command create_user or create_super user
class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, phone_number, password=None, **extra_fields):
        user = self.model(
            username=username,
            email=self.normalize_email(email),
            phone_number=phone_number,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
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
    phone_number = models.CharField(max_length=128, unique=False, null=True, blank=True, default=None)
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
    USERNAME_FIELD = 'id'
    REQUIRED_FIELDS = ['email', 'phone_number']

    # define table name
    class Meta:
        db_table = 'users'

    # Return data user object
    def __str__(self):
        return f"{self.id}"

    def save(self, *args, **kwargs):
        self.id = self.id.upper()
        if self.password is None or self.password == '':
            self.password = make_password(self.id.lower())
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


class Verify(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_verify = models.BooleanField(default=False)
    verify_code = models.CharField(max_length=64)
    verify_type = models.CharField(max_length=128, default=None)
    note = models.TextField(null=True, default=None)
    verify_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users_verify'


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


# Table/Model middleman of Group and User
class UserGroupPerm(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(GroupPerm, on_delete=models.CASCADE)
    allow = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users_user_group_perm'
