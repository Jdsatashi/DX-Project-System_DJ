from django.urls import path
from rest_framework.routers import DefaultRouter

from system.file_upload.api.views import GenericApiFileUpload, GenericApiFileContent
from utils.constants import actions_views, actions_detail

app_name = 'api_fileupload'

router = DefaultRouter()
router.register('genericview', GenericApiFileUpload, basename='api_file_upload')
router.register('genericview', GenericApiFileContent, basename='api_filecontent')

# Draft view
fileupload_view = GenericApiFileUpload.as_view(actions_views)
fileupload_detail = GenericApiFileUpload.as_view(actions_detail)

file_content_view = GenericApiFileContent.as_view(actions_views)
file_content_detail = GenericApiFileContent.as_view(actions_detail)


urlpatterns = [
    path('', fileupload_view),
    path('<pk>/', fileupload_detail),
    path('content/', file_content_view),
    path('content/<pk>/', file_content_detail)
]
