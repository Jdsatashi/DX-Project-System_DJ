from django.urls import path

from .views import *

app_name = 'khach_hang'

urlpatterns = [
    path('list', list_khach_hang, name='list_khach_hang'),
    path('create', create_khach_hang, name='create_khach_hang'),
]
