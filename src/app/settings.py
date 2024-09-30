import json
import os
import firebase_admin

from datetime import timedelta
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler

from celery.schedules import crontab
from pusher import Pusher

from utils.env import *
from firebase_admin import credentials

# Celery settings
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_BACKEND
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Ho_Chi_Minh'

CELERY_BEAT_SCHEDULE = {
    'send-daily-email-task': {
        'task': 'app.celery.send_daily_email_task',
        'schedule': crontab(hour="10", minute="15"),
        'args': (),
    },
}

# Email service
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = EMAIL_HOST_USER
EMAIL_HOST_PASSWORD = EMAIL_HOST_PASSWORD

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BASE_DIR.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = APP_SECRET

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = APP_DEBUG.lower() == 'true'

# Add acceptable host and CSRF
with open(os.path.join(PROJECT_DIR, 'exception.json')) as config_file:
    config = json.load(config_file)

ALLOWED_HOSTS = config.get('ALLOWED_HOSTS', [])
CSRF_TRUSTED_ORIGINS = config.get('CSRF_TRUSTED_ORIGINS', [])

# Firebase setup
FIREBASE_CONFIG_FILE = PROJECT_DIR / FIREBASE_JSON
cred = credentials.Certificate(FIREBASE_CONFIG_FILE)
firebase_admin.initialize_app(cred)

# Customize authentication
AUTH_USER_MODEL = 'account.User'

DJANGO_ALLOW_ASYNC_UNSAFE = True

SMS_SERVICE = {
    'host': SMS_SERVICE,
    'username': SMS_USERNAME,
    'sign': SMS_SIGN,
    'brand': SMS_BRAND,
    'type': SMS_TYPE
}

MY_APPS = [
    # My app
    'account',
    # User system structure
    # 'user_system.client_group',
    'user_system.client_profile',
    'user_system.employee_profile',
    'user_system.daily_email',
    # NVTT functions
    'marketing.company',
    'marketing.product',
    'marketing.price_list',
    'marketing.order',
    'marketing.livestream',
    'marketing.sale_statistic',
    'marketing.pick_number',
    'marketing.medias',
    # Default variables system setting
    'system_func'
]

# Application definition
INSTALLED_APPS = [
                     'django.contrib.admin',
                     'django.contrib.auth',
                     'django.contrib.contenttypes',
                     'django.contrib.sessions',
                     'django.contrib.messages',
                     'django.contrib.staticfiles',

                     # Django Rest Framework
                     'rest_framework',
                     'rest_framework_simplejwt.token_blacklist',
                     'drf_spectacular',
                     # Cors header
                     'corsheaders',
                     # System applications
                     'system.file_upload',
                     'system.status_group',
                     # Celery time management
                     'django_celery_beat',
                 ] + MY_APPS

pusher_client = Pusher(app_id=PUS_ID, key=PUS_KEY, secret=PUS_SECRET, cluster=PUS_CLUSTER, ssl=True)

# Create log folder
LOGGING_DIR = os.path.join(PROJECT_DIR, 'logs')
if not os.path.exists(LOGGING_DIR):
    os.makedirs(LOGGING_DIR)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] | [{levelname}] - {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'app_log_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(LOGGING_DIR, 'app.log'),
            'when': 'midnight',  # Log rotation at midnight
            'interval': 1,  # Rotate daily
            'backupCount': 10,  # Keep last 10 log files
            'formatter': 'verbose',
            'encoding': 'utf-8',
            'delay': True,
        },
        'system_log_file': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(LOGGING_DIR, 'system.log'),
            'when': 'midnight',  # Log rotation at midnight
            'interval': 1,  # Rotate daily
            'backupCount': 10,  # Keep last 10 log files
            'formatter': 'verbose',
            'encoding': 'utf-8',
            'delay': True,
        },
        'error_log_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(LOGGING_DIR, 'errors.log'),
            'when': 'midnight',
            'interval': 1,
            'backupCount': 10,
            'formatter': 'verbose',
            'encoding': 'utf-8',
            'delay': True,
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['system_log_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.server': {
            'handlers': ['system_log_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'app_log': {
            'handlers': ['app_log_file', 'system_log_file', 'error_log_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(seconds=int(TOKEN_LT)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(REF_TOKEN_LT)),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": True,

    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": "",
    "AUDIENCE": None,
    "ISSUER": None,
    "JSON_ENCODER": None,
    "JWK_URL": None,
    "LEEWAY": 0,

    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",

    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",

    "JTI_CLAIM": "jti",

    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),

    "TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainPairSerializer",
    "TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSerializer",
    "TOKEN_VERIFY_SERIALIZER": "rest_framework_simplejwt.serializers.TokenVerifySerializer",
    "TOKEN_BLACKLIST_SERIALIZER": "rest_framework_simplejwt.serializers.TokenBlacklistSerializer",
    "SLIDING_TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainSlidingSerializer",
    "SLIDING_TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSlidingSerializer",
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'account.middleware.CheckBlacklistMiddleware'
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# CORS_ALLOWED_ORIGINS = [
#     "http://localhost:8000",
#     "http://127.0.0.1:8000",
# ]

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True

ROOT_URLCONF = 'app.urls'

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

WSGI_APPLICATION = 'app.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

MSSQL = {
    'ENGINE': 'mssql',
    'NAME': MSSQL_DB,
    'HOST': MSSQL_HOST,
    'PORT': MSSQL_PORT,
    'USER': MSSQL_USER,
    'PASSWORD': MSSQL_PW,
    'OPTIONS': {'driver': 'ODBC Driver 18 for SQL Server'}
}

SQLITE = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': BASE_DIR / 'db.sqlite3',
}

POSTGRESQL = {
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': PGS_DB,
    'HOST': PGS_HOST,
    'PORT': PGS_PORT,
    'USER': PGS_USER,
    'PASSWORD': PGS_PASSWORD,
    'OPTIONS': {
        'sslmode': PGS_SSL,
    },
}

DATABASES = {
    'default': POSTGRESQL
}

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    # {
    #     'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    # },
]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

# Internationalization

LANGUAGE_CODE = 'en-us'  # 'vi'

TIME_ZONE = 'Asia/Ho_Chi_Minh'

USE_I18N = True

USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = '/static/'

STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR / 'static'),
    os.path.join(BASE_DIR / 'storage')
]

MEDIA_URL = '/storage/'

MEDIA_ROOT = BASE_DIR / 'storage'

if not os.path.exists(MEDIA_ROOT):
    os.makedirs(MEDIA_ROOT)

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
