from django.urls import path
from rest_framework.routers import DefaultRouter

from account.api.views import ApiAccount, otp_verify, phone_login_2, logout, check_token, \
    ApiUpdateUserProfile, ApiPerm, ApiGroupPerm, admin_login, ApiUpdateDeviceCode, ApiGetManageUser, GetUserManager, \
    otp_deactivate, verify_deactivate, ApiUpdateAccess

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

    path('export/', ApiAccount.as_view({'get': 'export_users'})),
    path('import/', ApiAccount.as_view({'post': 'import_users'})),

    path('group/', group_view),
    path('group/<pk>', group_detail),

    path('perm/', perm_view),
    path('perm/<pk>', perm_detail),

    path('login/', phone_login_2),
    path('logout/', logout),
    path('check-token/', check_token),
    path('profile/<pk>', ApiUpdateUserProfile.as_view({'get': 'retrieve', 'put': 'update'})),

    path('update-device-token/', ApiUpdateDeviceCode.as_view()),

    path('admin/', admin_login),
    path('manager/', ApiGetManageUser.as_view()),
    path('manager/access/', ApiUpdateAccess.as_view()),
    path('manager-list/', GetUserManager.as_view()),
    path('deactivate/otp/', otp_deactivate),
    path('deactivate/verify/', verify_deactivate),
]
