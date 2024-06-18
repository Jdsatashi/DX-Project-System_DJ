from django.urls import path

from marketing.medias.api.views import ApiNotification
from utils.constants import actions_views, actions_detail


app_name = 'api_media'


notify_view = ApiNotification.as_view(actions_views)
notify_detail = ApiNotification.as_view(actions_detail)

urlpatterns = [
    path('notify/', notify_view),
    path('notify/<pk>', notify_detail)
]
