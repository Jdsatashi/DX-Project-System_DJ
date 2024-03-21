# models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

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
		return user


# Self define user model attributes
class User(AbstractBaseUser, PermissionsMixin):
	usercode = models.CharField(primary_key=True, unique=True, null=False)
	username = models.CharField(max_length=255, unique=True, null=True, blank=True, default=None)
	email = models.EmailField(unique=True, null=True, blank=True, default=None)
	phone_number = models.CharField(max_length=128, unique=False, null=True, blank=True, default=None)
	password = models.CharField(max_length=256, null=False)
	khuVuc = models.CharField(max_length=100, null=True, blank=True, default=None)
	status = models.CharField(max_length=40, null=True, default=None)
	loaiUser = models.ForeignKey(UserType, to_field='loaiUser', null=True, blank=False, on_delete=models.SET_NULL)
	timestamp = models.DateTimeField(auto_now_add=True)
	nhomUser = models.ManyToManyField('NhomUser', blank=True, related_name='users_rela')
	quyenUser = models.ManyToManyField('QuyenHanUser', blank=True, related_name='users_rela')

	# System auth django attribute
	is_active = models.BooleanField(default=True)
	is_staff = models.BooleanField(default=False)
	is_superuser = models.BooleanField(default=False)
	last_login = models.DateTimeField(null=True, default=None)

	objects = CustomUserManager()

	# Required fields for create account command
	USERNAME_FIELD = 'username'
	REQUIRED_FIELDS = ['usercode', 'email', 'phone_number']

	# define table name
	class Meta:
		db_table = 'users'

	# Return data user object
	def __str__(self):
		return f"{self.usercode}"

	def save(self, *args, **kwargs):
		self.usercode = self.usercode.upper()
		super().save(*args, **kwargs)


# NhomUser as Role or Permission Groups
class NhomUser(models.Model):
	maNhom = models.CharField(primary_key=True, unique=True)
	tenNhom = models.CharField(max_length=255)
	moTa = models.TextField(null=True)
	timestamp = models.DateTimeField(auto_now_add=True)
	quyen = models.ManyToManyField('QuyenHanUser', related_name='nhomUser_rela')

	class Meta:
		db_table = 'users_nhomuser'


# QuyenHanUser as Permission
class QuyenHanUser(models.Model):
	maQuyenHan = models.CharField(primary_key=True, unique=True)
	tenQuyen = models.CharField(max_length=255, unique=True)
	moTa = models.TextField(null=True)
	timestamp = models.DateTimeField(auto_now_add=True)

	class Meta:
		db_table = 'users_quyenhan'
