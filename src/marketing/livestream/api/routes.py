from django.urls import path
from rest_framework.routers import DefaultRouter

from marketing.livestream.api.views import ApiLiveStream, ApiLiveStreamComment
from utils.constants import actions_views, actions_detail

app_name = 'api_livestream'

router = DefaultRouter()
router.register('genericview', ApiLiveStream, basename='api_livestream')
router.register('genericview', ApiLiveStreamComment, basename='api_livestream_comment')

livestream_views = ApiLiveStream.as_view(actions_views)
livestream_details = ApiLiveStream.as_view(actions_detail)

livestream_comment_views = ApiLiveStreamComment.as_view(actions_views)

urlpatterns = [
    path('', livestream_views, name='api_livestream'),
    path('<pk>', livestream_details, name='api_livestream_detail'),
    path('comments/', livestream_comment_views, name='api_livestream_comment'),
]
