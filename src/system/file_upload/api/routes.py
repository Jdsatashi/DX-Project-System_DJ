from django.urls import path
from rest_framework.routers import DefaultRouter

from system.file_upload.api.views import GenericApiFileUpload, GenericApiFileContent, ApiFileProductCate, ApiFileProduct
from utils.constants import actions_views, actions_detail

app_name = 'api_fileupload'

router = DefaultRouter()
router.register('genericview', GenericApiFileUpload, basename='api_file_upload')
router.register('genericview', GenericApiFileContent, basename='api_filecontent')
router.register('genericview', ApiFileProductCate, basename='api_file_product_cate')
router.register('genericview', ApiFileProduct, basename='api_file_product')

# Draft view
fileupload_view = GenericApiFileUpload.as_view(actions_views)
fileupload_detail = GenericApiFileUpload.as_view(actions_detail)

file_content_view = GenericApiFileContent.as_view(actions_views)
file_content_detail = GenericApiFileContent.as_view(actions_detail)

file_product_cate_view = ApiFileProductCate.as_view(actions_views)
file_product_cate_detail = ApiFileProductCate.as_view(actions_detail)

file_product_view = ApiFileProduct.as_view(actions_views)
file_product_detail = ApiFileProduct.as_view(actions_detail)

urlpatterns = [
    path('', fileupload_view),
    path('<pk>', fileupload_detail),
    path('content/', file_content_view),
    path('content/<pk>/', file_content_detail),
    path('product-category/', file_product_cate_view),
    path('product-category/<pk>/', file_product_cate_detail),
    path('product/', file_product_view),
    path('product/<pk>/', file_product_detail),
]
