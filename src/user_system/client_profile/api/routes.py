from django.urls import path
from rest_framework.routers import DefaultRouter

from user_system.client_profile.api.views import GenericApiClientGroup

app_name = 'client_profile'


client_group_view = GenericApiClientGroup.as_view({'get': 'list', 'post': 'create'})
client_group_detail_view = GenericApiClientGroup.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})


urlpatterns = [
    path('group/', client_group_view),
    path('group/<pk>', client_group_detail_view),
]
