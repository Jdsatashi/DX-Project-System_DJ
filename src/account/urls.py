from django.urls import path

from .api import insertDB
from .views import create_acc, list_acc

app_name = 'account'

urlpatterns = [
    path('', insertDB, name='insertDB'),
    path('create', create_acc, name='create_acc'),
    path('list', list_acc, name='list_acc')
]
