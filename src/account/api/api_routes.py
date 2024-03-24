from django.urls import path

from account.api.api import api_list_user, api_create_user, ApiRegister, ApiLogin, ApiTest, ApiLogout

app_name = 'api_account'

urlpatterns = [
    path('list', api_list_user, name='api_list_acc'),
    path('create', api_create_user, name='api_create_acc'),
    path('register', ApiRegister.as_view(), name='api_register'),
    path('login', ApiLogin.as_view(), name='api_login'),
    path('logout', ApiLogout.as_view(), name='api_logout'),
    path('test', ApiTest.as_view(), name='api_test')
]
