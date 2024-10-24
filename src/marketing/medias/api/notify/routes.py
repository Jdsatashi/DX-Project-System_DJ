from django.urls import path

from marketing.medias.api.notify.views import ApiNotification, ApiNotificationUser, TestMail
from utils.constants import actions_views, actions_detail


app_name = 'api_media'


notify_view = ApiNotification.as_view(actions_views)
notify_detail = ApiNotification.as_view(actions_detail)

notify_user_view = ApiNotificationUser.as_view({'get': 'list'})

urlpatterns = [
    path('notify/', notify_view),
    path('notify/<pk>', notify_detail),
    path('notify/user/<pk>', notify_user_view),
    path('mail/', TestMail.as_view())
]
