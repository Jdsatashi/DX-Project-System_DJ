from django.urls import path
from rest_framework.routers import DefaultRouter

from user_system.daily_email.api.views import ApiUserGetMail, ApiEmailDetail, ApiSendMail
from utils.constants import actions_views, actions_detail


app_name = 'daily_email'

router = DefaultRouter()

email_detail_view = ApiEmailDetail.as_view(actions_views)
email_detail_detail = ApiEmailDetail.as_view(actions_detail)

user_get_mail_view = ApiUserGetMail.as_view(actions_views)
user_get_mail_detail = ApiUserGetMail.as_view(actions_detail)


urlpatterns = [
    path('mail-detail/', email_detail_view),
    path('mail-detail/<pk>', email_detail_detail),

    path('user-get-mail/', user_get_mail_view),
    path('user-get-mail/<pk>', user_get_mail_detail),

    path('report-mail/', ApiSendMail.as_view())
]
