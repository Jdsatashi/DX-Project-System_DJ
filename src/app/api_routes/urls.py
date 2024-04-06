from django.urls import path

from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

from app.api_routes.handlers import CustomTokenObtainPairView

app_name = 'api_token'

urlpatterns = [
    path('', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
