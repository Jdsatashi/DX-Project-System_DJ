from django.urls import path
from rest_framework.routers import DefaultRouter

from account.api.views import api_create_user, ApiAccount

app_name = 'api_account'

router = DefaultRouter()
router.register('genericview', ApiAccount, basename='api_account')

# Draft view
account_view = ApiAccount.as_view({'get': 'list', 'post': 'create'})
account_detail = ApiAccount.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'})


urlpatterns = [
    path('register', api_create_user, name='api_create_acc'),
    path('', account_view),
    path('<int:pk>', account_detail)
]
