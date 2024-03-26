from django.urls import path, include

app_name = 'api_routes'

urlpatterns = [
    path('accounts/', include('account.api.api_routes', 'api_account')),
    path('token/', include('__init__.api_routes.urls', 'api_token')),
    path('draft/', include('draft.api.routes'), name='api_draft')
]
