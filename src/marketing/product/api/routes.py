from django.urls import path
from rest_framework.routers import DefaultRouter

from marketing.product.api.views import GenericApiProductType, GenericApiProductCategory, GenericApiRegistrationUnit, \
    GenericApiProducer, GenericApiRegistrationCert
from utils.constants import actions_views, actions_detail

app_name = 'api_account'

router = DefaultRouter()
router.register('genericview', GenericApiProductType, basename='api_product_type')
router.register('genericview', GenericApiRegistrationUnit, basename='api_register_unit')
router.register('genericview', GenericApiProducer, basename='api_register_producer')
router.register('genericview', GenericApiRegistrationCert, basename='api_register_cert')
router.register('genericview', GenericApiProductCategory, basename='api_category')

# Product Type view
prod_type_view = GenericApiProductType.as_view(actions_views)
prod_type_detail = GenericApiProductType.as_view(actions_detail)

register_unit_view = GenericApiProductType.as_view(actions_views)
register_unit_detail = GenericApiProductType.as_view(actions_detail)

producer_view = GenericApiProductType.as_view(actions_views)
producer_detail = GenericApiProductType.as_view(actions_detail)

register_cert_view = GenericApiProductType.as_view(actions_views)
register_cert_detail = GenericApiProductType.as_view(actions_detail)

prod_cate_view = GenericApiProductType.as_view(actions_views)
prod_cate_detail = GenericApiProductType.as_view(actions_detail)

urlpatterns = [
    # Product Type urls
    path('type/', prod_type_view),
    path('type/<pk>/', prod_type_detail),
    # Product register groups urls
    path('register/unit/', register_unit_view),
    path('register/unit/<pk>/', register_unit_detail),
    path('register/producer/', producer_view),
    path('register/producer/<pk>/', producer_detail),
    path('register/certificate/', register_cert_view),
    path('register/certificate/<pk>/', register_cert_detail),
    # Product category urls
    path('category/', prod_cate_view),
    path('category/<pk>/', prod_cate_detail),
]
