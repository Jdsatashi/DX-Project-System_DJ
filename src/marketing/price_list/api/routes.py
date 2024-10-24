from django.urls import path
from rest_framework.routers import DefaultRouter

from marketing.price_list.api.views import GenericApiPriceList, ApiSpecialOffer, ApiSpecialOfferConsider, \
    ApiImportProductPL, ApiImportProductSO, ApiSOProduct, ApiPLProduct
from utils.constants import actions_views, actions_detail

app_name = 'api_price_list'

router = DefaultRouter()
router.register('genericview', GenericApiPriceList, basename='api_price_list')
router.register('genericview', ApiSpecialOffer, basename='api_special_offer')

price_list_views = GenericApiPriceList.as_view(actions_views)
price_list_details = GenericApiPriceList.as_view(actions_detail)

pl_product_views = ApiPLProduct.as_view(actions_views)
pl_product_details = ApiPLProduct.as_view(actions_detail)

special_offer_views = ApiSpecialOffer.as_view(actions_views)
special_offer_details = ApiSpecialOffer.as_view(actions_detail)

urlpatterns = [
    path('', price_list_views, name='api_price_list_view'),
    path('<pk>', price_list_details, name='api_price_list_detail'),

    path('product/', pl_product_views, name='api_price_list_view'),
    path('product/<pk>', pl_product_details, name='api_price_list_detail'),

    path('get/now/', GenericApiPriceList.as_view({'get': 'now'}), name='api_price_list_now'),
    path('special-offer/', special_offer_views, name='api_special_offer_view'),
    path('special-offer/<pk>', special_offer_details, name='api_special_offer_detail'),
    path('special-offer/consider/', ApiSpecialOfferConsider.as_view({'get': 'list'}), name='api_special_offer_consider'),
    path('import/', ApiImportProductPL.as_view(), name='api_price_list_import'),
    path('special-offer/import/', ApiImportProductSO.as_view()),

    path('special-offer/product/', ApiSOProduct.as_view(actions_views)),
    path('special-offer/product/<pk>', ApiSOProduct.as_view(actions_detail)),
    path('special-offer/export-products/<pk>', ApiSpecialOffer.as_view({'get': 'export_so_product'})),
    path('special-offer/export-users/<pk>', ApiSpecialOffer.as_view({'get': 'export_users'})),
    path('special-offer/import-consider/', ApiSpecialOffer.as_view({'post': 'import_multi_so'})),

    path('<pk>/export-products/', GenericApiPriceList.as_view({'get': 'export_products'})),
    path('<pk>/export-users/', GenericApiPriceList.as_view({'get': 'export_users'})),
]
