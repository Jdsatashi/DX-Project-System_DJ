from django.urls import path

from account.api.views import api_create_user, ApiRegister

app_name = 'api_account'

urlpatterns = [
    path('register', api_create_user, name='api_create_acc'),
    path('create', ApiRegister.as_view(), name='api_register'),
]
