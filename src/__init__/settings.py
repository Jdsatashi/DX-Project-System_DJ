from pathlib import Path

import os

import dotenv

dotenv.load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', True)

ALLOWED_HOSTS = []

# Customize authentication
AUTH_USER_MODEL = 'account.User'

# Application definition
INSTALLED_APPS = [
	'django.contrib.admin',
	'django.contrib.auth',
	'django.contrib.contenttypes',
	'django.contrib.sessions',
	'django.contrib.messages',
	'django.contrib.staticfiles',

	# My app
	'draft',
	'account',
	# Old data app
	'qlsx.khach_hang',
]

LOGGING = {
	"version": 1,
	"disable_existing_loggers": False,
	"handlers": {
		"console": {
			"class": "logging.StreamHandler",
		},
	},
	"root": {
		"handlers": ["console"],
		"level": "INFO",
	},
}

MIDDLEWARE = [
	'django.middleware.security.SecurityMiddleware',
	'django.contrib.sessions.middleware.SessionMiddleware',
	'django.middleware.common.CommonMiddleware',
	'django.middleware.csrf.CsrfViewMiddleware',
	'django.contrib.auth.middleware.AuthenticationMiddleware',
	'django.contrib.messages.middleware.MessageMiddleware',
	'django.middleware.clickjacking.XFrameOptionsMiddleware',
	'account.middlewares.CustomAuthMiddleware'
]

ROOT_URLCONF = '__init__.urls'

TEMPLATES = [
	{
		'BACKEND': 'django.template.backends.django.DjangoTemplates',
		'DIRS': [BASE_DIR / 'templates'],
		'APP_DIRS': True,
		'OPTIONS': {
			'context_processors': [
				'django.template.context_processors.debug',
				'django.template.context_processors.request',
				'django.contrib.auth.context_processors.auth',
				'django.contrib.messages.context_processors.messages',
			],
		},
	},
]

WSGI_APPLICATION = '__init__.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
	'default': {
		'ENGINE': 'mssql',
		'NAME': os.environ['DB_NAME'],
		'HOST': os.environ['DB_HOST'],
		'PORT': os.environ['DB_PORT'],
		'USER': os.environ['DB_USER'],
		'PASSWORD': os.environ['DB_PASSWORD'],
		"OPTIONS": {"driver": "ODBC Driver 17 for SQL Server"}
		# 'OPTIONS': {
		# 	'sslmode': os.environ['DB_SSLMODE'],
		# 	'options': f'?options=endpoint%3D{os.environ["DB_ENDPOINT_ID"]}',
		# },
	}
	# 'default': {
	# 	'ENGINE': 'django.db.backends.sqlite3',
	# 	'NAME': BASE_DIR / 'db.sqlite3',
	# }
}

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
	{
		'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
	},
	{
		'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
	},
	{
		'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
	},
	{
		'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
	},
]

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Ho_Chi_Minh'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'

STATICFILES_DIRS = [BASE_DIR / 'static']

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
