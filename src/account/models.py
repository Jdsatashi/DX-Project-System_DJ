# models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


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
		return self.create_user(username, email, phone_number, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
	usercode = models.AutoField(primary_key=True)
	username = models.CharField(max_length=255, unique=True)
	email = models.EmailField(unique=True)
	phone_number = models.CharField(max_length=15, unique=True)
	is_active = models.BooleanField(default=True)
	is_staff = models.BooleanField(default=False)
	timestamp = models.DateTimeField(auto_now_add=True)
	
	objects = CustomUserManager()
	
	USERNAME_FIELD = 'username'
	REQUIRED_FIELDS = ['email', 'phone_number']


class Role(models.Model):
	name = models.CharField(max_length=255, unique=True)
	description = models.TextField()
	timestamp = models.DateTimeField(auto_now_add=True)
	permissions = models.ManyToManyField('Permission', related_name='roles')


class Permission(models.Model):
	name = models.CharField(max_length=255, unique=True)
	description = models.TextField()
	timestamp = models.DateTimeField(auto_now_add=True)
