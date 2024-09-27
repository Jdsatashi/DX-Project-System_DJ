from django.urls import path
from rest_framework.routers import DefaultRouter

from marketing.product.api.views import GenericApiProductType, GenericApiProductCategory, GenericApiRegistrationUnit, \
    GenericApiProducer, GenericApiRegistrationCert, GenericApiProduct, GenericApiCategoryDetail, ApiProductId, \
    ApiUseFor, ApiUseObject
from utils.constants import actions_views, actions_detail

app_name = 'api_account'

router = DefaultRouter()

# Product Type view
prod_type_view = GenericApiProductType.as_view(actions_views)
prod_type_detail = GenericApiProductType.as_view(actions_detail)

register_unit_view = GenericApiRegistrationUnit.as_view(actions_views)
register_unit_detail = GenericApiRegistrationUnit.as_view(actions_detail)

producer_view = GenericApiProducer.as_view(actions_views)
producer_detail = GenericApiProducer.as_view(actions_detail)

register_cert_view = GenericApiRegistrationCert.as_view(actions_views)
register_cert_detail = GenericApiRegistrationCert.as_view(actions_detail)

prod_cate_view = GenericApiProductCategory.as_view(actions_views)
prod_cate_detail = GenericApiProductCategory.as_view(actions_detail)

cate_detail_view = GenericApiCategoryDetail.as_view(actions_views)
cate_detail_detail = GenericApiCategoryDetail.as_view(actions_detail)

prod_view = GenericApiProduct.as_view(actions_views)
prod_detail = GenericApiProduct.as_view(actions_detail)

use_object_view = ApiUseObject.as_view(actions_views)
use_object_detail = ApiUseObject.as_view(actions_detail)

use_for_view = ApiUseFor.as_view(actions_views)
use_for_detail = ApiUseFor.as_view(actions_detail)

urlpatterns = [
    # Product Type urls
    path('type/', prod_type_view),
    path('type/<pk>', prod_type_detail),
    # Product register groups urls
    path('register/unit/', register_unit_view),
    path('register/unit/<pk>', register_unit_detail),
    path('register/producer/', producer_view),
    path('register/producer/<pk>', producer_detail),
    path('register/certificate/', register_cert_view),
    path('register/certificate/<pk>', register_cert_detail),
    # Product category urls
    path('categories/', prod_cate_view),
    path('categories/<pk>', prod_cate_detail),
    path('category/detail/', cate_detail_view),
    path('category/detail/<pk>', cate_detail_detail),
    # Product urls
    path('', prod_view),
    path('<pk>', prod_detail),
    path('export/', GenericApiProduct.as_view({'get': 'export_products'})),

    path('categories/use-object/', use_object_view),
    path('categories/use-object/<pk>', use_object_detail),

    path('categories/use-for/', use_for_view),
    path('categories/use-for/<pk>', use_for_detail),

    path('get-id/', ApiProductId.as_view({'get': 'list'}))
]
