# models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

from user_system.user_type.models import UserType


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
		extra_fields.setdefault('is_superuser', True)
		return self.create_user(username, email, phone_number, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
	usercode = models.CharField(primary_key=True, unique=True)
	username = models.CharField(max_length=255, unique=True, null=True)
	email = models.EmailField(unique=True, null=True)
	phone_number = models.CharField(max_length=15, unique=True, null=True)
	khuVuc = models.CharField(max_length=100, null=True, blank=True)
	status = models.CharField(max_length=40, null=True)
	loaiUser = models.ForeignKey(UserType, to_field='loaiUser', null=False, blank=False, on_delete=models.SET_NULL)
	timestamp = models.DateTimeField(auto_now_add=True)
	nhomUser = models.ManyToManyField('NhomUser', blank=True, related_name='users')
	quyenUser = models.ManyToManyField('QuyenHanUser', blank=True, related_name='users')

	objects = CustomUserManager()

	USERNAME_FIELD = 'username'


class NhomUser(models.Model):
	maNhom = models.CharField(primary_key=True, unique=True)
	tenNhom = models.CharField(max_length=255)
	moTa = models.TextField(null=True)
	timestamp = models.DateTimeField(auto_now_add=True)
	permissions = models.ManyToManyField('QuyenHanUser', related_name='nhomUser')


class QuyenHanUser(models.Model):
	maQuyenHan = models.CharField(primary_key=True, unique=True)
	tenQuyen = models.CharField(max_length=255, unique=True)
	moTa = models.TextField(null=True)
	timestamp = models.DateTimeField(auto_now_add=True)
