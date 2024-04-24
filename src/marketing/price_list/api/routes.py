from django.urls import path
from rest_framework.routers import DefaultRouter

from marketing.price_list.api.views import GenericApiPriceList
from utils.constants import actions_views, actions_detail

app_name = 'api_price_list'

router = DefaultRouter()
router.register('genericview', GenericApiPriceList, basename='api_account')

price_list_views = GenericApiPriceList.as_view(actions_views)
price_list_details = GenericApiPriceList.as_view(actions_detail)

urlpatterns = [
    path('', price_list_views, name='api_price_list_view'),
    path('<pk>/', price_list_details, name='api_price_list_detail'),
]
