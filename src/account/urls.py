from django.urls import path

from .api import insertDB

app_name = 'account'

urlpatterns = [
    path('', insertDB, name='insertDB')
]
