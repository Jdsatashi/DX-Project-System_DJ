import os

import dotenv

dotenv.load_dotenv()

# App environment variable
APP_SERVER = os.environ.get('APP_SERVER')
APP_DEBUG = os.environ.get('DEBUG', True)
APP_SECRET = os.environ.get('SECRET_KEY')

# SMS connection
SMS_SERVICE = os.environ.get('SMS_SERVICE')
SMS_USERNAME = os.environ.get('SMS_USERNAME')
SMS_SIGN = os.environ.get('SMS_SIGN')
SMS_BRAND = os.environ.get('SMS_BRAND')
SMS_TYPE = os.environ.get('SMS_TYPE')

# MSSQL connection
MSSQL_DB = os.environ.get('DB_NAME')
MSSQL_HOST = os.environ.get('DB_HOST')
MSSQL_PORT = os.environ.get('DB_PORT')
MSSQL_USER = os.environ.get('DB_USER')
MSSQL_PW = os.environ.get('DB_PASSWORD')

# PostgreSql connection
PGS_DB = os.environ.get('PGS_DB')
PGS_HOST = os.environ.get('PGS_HOST')
PGS_PORT = os.environ.get('PGS_PORT')
PGS_USER = os.environ.get('PGS_USER')
PGS_PASSWORD = os.environ.get('PGS_PASSWORD')
PGS_SSL = os.environ.get('PGS_SSL')

# Old MSSQL Server
OLD_SQL_HOST = os.environ.get('MSSQL_HOST')
OLD_SQL_DB = os.environ.get('MSSQL_DATABASE')
OLD_SQL_USER = os.environ.get('MSSQL_USER')
OLD_SQL_PW = os.environ.get('MSSQL_PASSWORD')

# Pusher config
PUS_ID = os.environ.get('PUSHER_ID')
PUS_KEY = os.environ.get('PUSHER_KEY')
PUS_SECRET = os.environ.get('PUSHER_SECRET')
PUS_CLUSTER = os.environ.get('PUSHER_CLUSTER')

# Token life time
TOKEN_LT = os.environ.get('TOKEN_LIFE')
REF_TOKEN_LT = os.environ.get('REF_TOKEN_LIFE')

# Firebase
FIREBASE_JSON = os.environ.get('FIREBASE_KEY')

ALLOW_HOSTS = os.getenv('ALLOWED_HOSTS', '["localhost"]')
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', '["http://localhost"]')
