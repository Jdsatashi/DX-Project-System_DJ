from django.urls import path
from rest_framework.routers import DefaultRouter

from user_system.user_type.api.views import UserTypeApiView, GenericApiUserType

app_name = 'user_type'

router = DefaultRouter()
router.register('genericview', GenericApiUserType, basename='api_user_type')

# Draft view
types_view = GenericApiUserType.as_view({'get': 'list', 'post': 'create'})
type_detail_view = GenericApiUserType.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})


urlpatterns = [
    path('', types_view),
    path('<pk>/', type_detail_view),
]
