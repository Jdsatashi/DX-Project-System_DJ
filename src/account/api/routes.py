from django.urls import path
from rest_framework.routers import DefaultRouter

from account.api.views import api_create_user, ApiAccount, otp_verify, RegisterSMS, phone_login, logout, check_token

app_name = 'api_account'

router = DefaultRouter()
router.register('genericview', ApiAccount, basename='api_account')

# Draft view
account_view = ApiAccount.as_view({'get': 'list', 'post': 'create'})
account_detail = ApiAccount.as_view(
    {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'})

urlpatterns = [
    # path('register/', RegisterSMS.as_view(), name='api_register'),
    path('verify/<pk>/', otp_verify, name='api_verify'),
    path('', account_view),
    path('<pk>', account_detail),
    path('login/', phone_login),
    path('logout/', logout),
    path('check-token/', check_token)
]
