from django.urls import path
from rest_framework.routers import DefaultRouter

from marketing.pick_number.api.views import ApiEventNumber, ApiUserJoinEvent, ApiNumberList, ApiPickNumber
from utils.constants import actions_views, actions_detail

app_name = "api_pick_number"

# router = DefaultRouter()
# router.register('genericview', ApiEventNumber, basename='api_event_number')
# router.register('genericview', ApiUserJoinEvent, basename='api_event_user')

event_number_views = ApiEventNumber.as_view(actions_views)
event_number_details = ApiEventNumber.as_view(actions_detail)

event_user_views = ApiUserJoinEvent.as_view(actions_views)
event_user_details = ApiUserJoinEvent.as_view(actions_detail)

event_number_list_views = ApiNumberList.as_view(actions_views)
event_number_list_details = ApiNumberList.as_view(actions_detail)

pick_number = ApiPickNumber.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update'})


urlpatterns = [
    path('', event_number_views, name='api_event_number_view'),
    path('<pk>', event_number_details, name='api_event_number_detail'),

    path('user-info/', event_user_views, name='api_event_user_view'),
    path('user-info/<pk>', event_user_details, name='api_event_user_detail'),

    path('user-info/pick/<pk>', pick_number, name='api_event_user_pick'),

    path('number-list/', event_number_list_views, name='api_event_number_views'),
    path('number-list/<pk>', event_number_list_details, name='api_event_number_details'),
]
