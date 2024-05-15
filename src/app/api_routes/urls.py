from django.urls import path
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
)

from app.api_routes.handlers import CustomTokenObtainPairView, CustomTokenRefreshView

app_name = 'api_token'

urlpatterns = [
    path('', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('blacklist/', TokenBlacklistView.as_view(), name='token_blacklist')
]
