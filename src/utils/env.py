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
MSSQL_DB = os.environ['DB_NAME']
MSSQL_HOST= os.environ['DB_HOST']
MSSQL_PORT = os.environ['DB_PORT']
MSSQL_USER = os.environ['DB_USER']
MSSQL_PW = os.environ['DB_PASSWORD']

# PostgreSql connection
PGS_DB = os.environ['PGS_DB']
PGS_HOST = os.environ['PGS_HOST']
PGS_PORT = os.environ['PGS_PORT']
PGS_USER = os.environ['PGS_USER']
PGS_PASSWORD = os.environ['PGS_PASSWORD']
PGS_SSL = os.environ['PGS_SSL']

# Old MSSQL Server
OLD_SQL_HOST = os.environ.get('MSSQL_HOST')
OLD_SQL_DB = os.environ.get('MSSQL_DATABASE')
OLD_SQL_USER = os.environ.get('MSSQL_USER')
OLD_SQL_PW = os.environ.get('MSSQL_PASSWORD')

# Token life time
TOKEN_LT = os.environ.get('TOKEN_LIFE')
REF_TOKEN_LT = os.environ.get('REF_TOKEN_LIFE')