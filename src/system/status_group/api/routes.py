from django.urls import path

from system.status_group.api.views import ApiStatus

app_name = 'api_status'

urlpatterns = [
    path('', ApiStatus.as_view())
]
