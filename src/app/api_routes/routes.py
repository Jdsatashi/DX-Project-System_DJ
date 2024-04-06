from django.urls import path, include

app_name = 'api_routes'

urlpatterns = [
    path('accounts/', include('account.api.routes', 'api_account')),
    path('token/', include('app.api_routes.urls', 'api_token')),
    path('draft/', include('draft.api.routes'), name='api_draft'),
    path('user-type/', include('user_system.user_type.api.routes', 'api_user_type'))
]
