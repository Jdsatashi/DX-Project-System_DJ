from django.urls import path, include
from django.views.generic import TemplateView

from app.api_routes.handlers import ApiContentType

app_name = 'api_routes'

urlpatterns = [
    path('', TemplateView.as_view(template_name='layouts/api_docs.html', extra_context={'schema_url': 'api_schema'}), name='api_docs'),
    path('content-type', ApiContentType.as_view(), name="api-content_type"),
    path('accounts/', include('account.api.routes', 'api_account')),
    path('token/', include('app.api_routes.urls', 'api_token')),
    path('draft/', include('draft.api.routes'), name='api_draft'),
    path('user-type/', include('user_system.user_type.api.routes', 'api_user_type')),
    path('client-group/', include('user_system.client_group.api.routes', 'api_client_group')),
    path('employees/', include('user_system.employee_profile.api.routes', 'api_employee_profile')),
    path('file-upload/', include('system.file_upload.api.routes', 'api_file_upload')),
    path('status/', include('system.status_group.api.routes', 'api_status')),

    path('products/', include('marketing.product.api.routes', 'api_products'))
]
