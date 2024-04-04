# models.py
from django.contrib import admin
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import Permission

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
        quyens = Quyen.objects.all()
        for i, q in enumerate(quyens):
            user.quyenUser.add(q)
        return user


# Self define user model attributes
class User(AbstractBaseUser, PermissionsMixin):
    id = models.CharField(primary_key=True, unique=True, null=False)
    username = models.CharField(max_length=255, unique=True, null=True, blank=True, default=None)
    email = models.EmailField(unique=False, null=True, blank=True, default=None)
    phone_number = models.CharField(max_length=128, unique=False, null=True, blank=True, default=None)
    password = models.CharField(max_length=256, null=False)
    khuVuc = models.CharField(max_length=100, null=True, blank=True, default=None)
    status = models.CharField(max_length=40, null=True, default=None)
    loaiUser = models.ForeignKey(UserType, to_field='loaiUser', null=True, blank=False, on_delete=models.SET_NULL)
    timestamp = models.DateTimeField(auto_now_add=True)
    nhomUser = models.ManyToManyField('NhomQuyen', through='NhomQuyenUser', blank=True, related_name='users_rela')
    quyenUser = models.ManyToManyField('Quyen', through='QuyenUser', blank=True, related_name='users_rela')

    # System auth django attribute
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True, default=None)

    objects = CustomUserManager()

    # Required fields for create account command
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['id', 'email', 'phone_number']

    # define table name
    class Meta:
        db_table = 'users'

    # Return data user object
    def __str__(self):
        return f"{self.id}"

    def save(self, *args, **kwargs):
        self.id = self.id.upper()
        super().save(*args, **kwargs)

    def has_quyen(self, permission):
        return self.quyenUser.filter(name=permission).exists()

    def is_allow(self, permission):
        has_quyen = self.has_quyen(permission)
        if has_quyen:
            quyen = self.quyenUser.filter(name=permission).first()
            quyen_user = QuyenUser.objects.get(user=self, quyen=quyen)
            return quyen_user.allow
        return has_quyen

    def has_nhom_with_quyen(self, permission):
        nhom_user = self.nhomUser.all()
        valid = False
        for nhom in nhom_user:
            valid = nhom.nhom_has_quyen(permission)
            if valid:
                break
        return valid


class XacThuc(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    xac_thuc = models.BooleanField(default=False)
    ma_xac_thuc = models.CharField(max_length=64)
    loai_xac_thuc = models.CharField(max_length=128, default=None)
    moTa = models.TextField(null=True, default=None)
    time_xac_thuc = models.DateTimeField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users_xac_thuc'


# Quyen as known as Permissions
class Quyen(models.Model):
    name = models.CharField(max_length=255, primary_key=True)
    mota = models.TextField(null=True, default=None, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    content_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=255)
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        db_table = 'users_quyen'


# NhomQuyen as a Permissions Group or Roles User
class NhomQuyen(models.Model):
    name = models.CharField(max_length=255, primary_key=True)
    mota = models.TextField(null=True, default=None, blank=True)
    quyen = models.ManyToManyField(Quyen, blank=True)
    allow = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users_nhom'

    def nhom_has_quyen(self, permission):
        quyen = self.quyen.filter(name=permission)
        return quyen.exists() and self.allow


# Table/Model middleman of Quyen and User
class QuyenUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quyen = models.ForeignKey(Quyen, on_delete=models.CASCADE)
    allow = models.BooleanField(default=True)

    class Meta:
        db_table = 'users_quyen_user'


# Table/Model middleman of Nhom and User
class NhomQuyenUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nhom = models.ForeignKey(NhomQuyen, on_delete=models.CASCADE)
    allow = models.BooleanField(default=True)

    class Meta:
        db_table = 'users_nhomQuyen_user'
