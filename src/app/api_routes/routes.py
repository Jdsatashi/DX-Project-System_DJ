from django.urls import path, include
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularSwaggerView, SpectacularRedocView

from app.api_routes.handlers import ApiContentType

app_name = 'api_routes'

urlpatterns = [
    path('', SpectacularSwaggerView.as_view(url_name='api-schema'), name='swagger-ui'),
    path('redocs/', SpectacularRedocView.as_view(url_name='api-schema'), name='redoc'),

    path('content-type/', ApiContentType.as_view(), name="api-content_type"),
    path('accounts/', include('account.api.routes', 'api_account')),
    path('token/', include('app.api_routes.urls', 'api_token')),
    path('client/', include('user_system.client_profile.api.routes', 'client_profile')),
    path('employees/', include('user_system.employee_profile.api.routes', 'api_employee_profile')),
    path('file-upload/', include('system.file_upload.api.routes', 'api_file_upload')),
    path('status/', include('system.status_group.api.routes', 'api_status')),

    path('products/', include('marketing.product.api.routes', 'api_products')),
    path('company/', include('marketing.company.api.routes', 'api_company')),
    path('price-list/', include('marketing.price_list.api.routes', 'api_price_list')),
    path('order/', include('marketing.order.api.routes', 'api_order')),
    path('livestream/', include('marketing.livestream.api.routes', 'api_livestream')),
    path('sale-statistic/', include('marketing.sale_statistic.api.routes', 'api_sale_statistic')),
    path('event-number/', include('marketing.pick_number.api.routes', 'api_pick_number')),
    path('media/', include('marketing.medias.api.notify.routes', 'api_media')),
    path('media/banner/', include('marketing.medias.api.banner.routes', 'api_banner')),
    path('system-config/', include('system_func.api.routes')),
]
