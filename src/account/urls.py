from django.urls import path

from .views import create_acc, list_acc, login_acc

app_name = 'account'

urlpatterns = [
    path('create/', create_acc, name='create_acc'),
    path('list/', list_acc, name='list_acc'),
    path('login/', login_acc, name='login_acc')
]
