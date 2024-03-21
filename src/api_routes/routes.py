from django.urls import path, include

app_name = 'api_routes'

urlpatterns = [
    path('accounts/', include('account.api_routes', 'api_account'))
]
