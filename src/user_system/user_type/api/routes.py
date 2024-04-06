from django.urls import path

from user_system.user_type.api.views import UserTypeApiView

app_name = 'user_type'

urlpatterns = [
    path('', UserTypeApiView.as_view(), name='get_user_type')
]
