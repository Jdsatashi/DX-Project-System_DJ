from django.urls import path
from rest_framework.routers import DefaultRouter

from marketing.order.api.views import GenericApiOrder
from utils.constants import actions_views, actions_detail

app_name = "api_order"

router = DefaultRouter()
router.register('genericview', GenericApiOrder, basename='api_order')

order_views = GenericApiOrder.as_view(actions_views)
order_details = GenericApiOrder.as_view(actions_detail)


urlpatterns = [
    path('', order_views, name='api_order_view'),
    path('<pk>/', order_details, name='api_order_detail'),
]
