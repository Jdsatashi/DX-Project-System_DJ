from django.urls import path
from rest_framework.routers import DefaultRouter

from account.api.views import ApiAccount, otp_verify, phone_login_2, logout, check_token, \
    ApiUpdateUserProfile, ApiPerm, ApiGroupPerm

app_name = 'api_account'

router = DefaultRouter()
router.register('genericview', ApiAccount, basename='api_account')
router.register('genericview', ApiGroupPerm, basename='api_group_perm')
router.register('genericview', ApiPerm, basename='api_perm')

# Draft view
account_view = ApiAccount.as_view({'get': 'list', 'post': 'create'})
account_detail = ApiAccount.as_view(
    {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'})

group_view = ApiGroupPerm.as_view({'get': 'list', 'post': 'create'})
group_detail = ApiGroupPerm.as_view(
    {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'})

perm_view = ApiPerm.as_view({'get': 'list'})
perm_detail = ApiPerm.as_view(
    {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'})

urlpatterns = [
    # path('register/', RegisterSMS.as_view(), name='api_register'),
    path('verify/<pk>/', otp_verify, name='api_verify'),
    path('', account_view),
    path('<pk>', account_detail),

    path('group/', group_view),
    path('group/<pk>', group_detail),

    path('perm/', perm_view),
    path('perm/<pk>', perm_detail),

    path('login/', phone_login_2),
    path('logout/', logout),
    path('check-token/', check_token),
    path('profile/<pk>', ApiUpdateUserProfile.as_view({'get': 'retrieve', 'put': 'update'}))
]
