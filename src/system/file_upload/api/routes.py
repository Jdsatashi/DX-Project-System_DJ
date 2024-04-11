from django.urls import path
from rest_framework.routers import DefaultRouter

from system.file_upload.api.views import GenericApiFileUpload

app_name = 'api_fileupload'

router = DefaultRouter()
router.register('genericview', GenericApiFileUpload, basename='api_fileupload')

# Draft view
fileupload_view = GenericApiFileUpload.as_view({'get': 'list', 'post': 'create'})
fileupload_detail = GenericApiFileUpload.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'})


urlpatterns = [
    path('', fileupload_view),
    path('<pk>', fileupload_detail)
]
