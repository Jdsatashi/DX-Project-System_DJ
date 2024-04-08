from django.urls import path
from rest_framework.routers import DefaultRouter
from user_system.client_group.api.views import GenericApiClientGroup

app_name = 'client_group'

router = DefaultRouter()
router.register('genericview', GenericApiClientGroup, basename='api_client_group')

# Draft view
client_group_view = GenericApiClientGroup.as_view({'get': 'list', 'post': 'create'})
client_group_detail_view = GenericApiClientGroup.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})


urlpatterns = [
    path('', client_group_view),
    path('<pk>/', client_group_detail_view),
]
