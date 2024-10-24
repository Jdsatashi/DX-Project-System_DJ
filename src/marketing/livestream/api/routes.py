from django.urls import path
from rest_framework.routers import DefaultRouter

from marketing.livestream.api.views import (ApiLiveStream, ApiLiveStreamComment,
                                            ApiLiveStatistic, ApiLiveTracking,
                                            ApiLiveStreamDetailComment, ApiPeekView, JoinPeekView, LeavePeekView,
                                            ApiLiveOfferRegister, CheckLiveStreamRegistrationView, ExportLiveReport)
from utils.constants import actions_views, actions_detail

app_name = 'api_livestream'

router = DefaultRouter()
router.register('genericview', ApiLiveStream, basename='api_livestream')
router.register('genericview', ApiLiveStreamComment, basename='api_livestream_comment')
# router.register('genericview', ApiLiveProduct, basename='api_livestream_product')
# router.register('genericview', ApiLiveProductList, basename='api_livestream_product_list')
router.register('genericview', ApiLiveStatistic, basename='api_livestream_statistic')
router.register('genericview', ApiLiveTracking, basename='api_livestream_tracking')
router.register('genericview', ApiLiveStreamDetailComment, basename='api_livestream_detail_comment')
router.register('genericview', ApiPeekView, basename='api_peek_view')
router.register('genericview', ApiLiveOfferRegister, basename='api_offer_register')
# router.register('genericview', ApiLiveOrder, basename='api_livestream_order')

livestream_views = ApiLiveStream.as_view(actions_views)
livestream_details = ApiLiveStream.as_view(actions_detail)

# live_product_views = ApiLiveProduct.as_view(actions_views)
# live_product_details = ApiLiveProduct.as_view(actions_detail)
#
# live_product_list_views = ApiLiveProductList.as_view(actions_views)
# live_product_list_details = ApiLiveProductList.as_view(actions_detail)

live_statistic_views = ApiLiveStatistic.as_view(actions_views)
live_statistic_details = ApiLiveStatistic.as_view(actions_detail)

live_views = ApiLiveTracking.as_view(actions_views)
live_details = ApiLiveTracking.as_view(actions_detail)

# live_order_views = ApiLiveOrder.as_view(actions_views)
# live_order_details = ApiLiveOrder.as_view(actions_detail)

live_peekview_views = ApiPeekView.as_view(actions_views)
live_peekview_details = ApiPeekView.as_view(actions_detail)

live_offer_register_views = ApiLiveOfferRegister.as_view(actions_views)
live_offer_register_details = ApiLiveOfferRegister.as_view(actions_detail)

livestream_comment_views = ApiLiveStreamComment.as_view(actions_views)

livestream_detail_comment = ApiLiveStreamDetailComment.as_view({'get': 'list'})



urlpatterns = [
    path('', livestream_views, name='api_livestream'),
    path('<pk>', livestream_details, name='api_livestream_detail'),
    path('<pk>/report-export/', ExportLiveReport.as_view(), name='api_livestream_detail'),
    path('<pk>/export-users/', ApiLiveStream.as_view({'get': 'export_users'})),
    path('comments/', livestream_comment_views, name='api_livestream_comment'),
    path('stream-comments/<livestream_id>', livestream_detail_comment, name='api_livestream_detail_comment'),
    # path('products/', live_product_views, name='api_livestream_product'),
    # path('products/<pk>', live_product_details, name='api_livestream_product_detail'),
    # path('products-list/', live_product_list_views, name='api_livestream_product_list'),
    # path('products-list/<pk>', live_product_list_details, name='api_livestream_product_list_detail'),
    path('statistic/', live_statistic_views, name='api_livestream_statistic'),
    path('statistic/<pk>', live_statistic_details, name='api_livestream_statistic_detail'),
    path('tracking/', live_views, name='api_livestream_tracking'),
    path('tracking/<pk>', live_details, name='api_livestream_tracking_detail'),
    path('peekview/', live_peekview_views, name='api_peek_view'),
    path('peekview/<pk>', live_peekview_details, name='api_peek_view_detail'),
    path('peekview/join/', JoinPeekView.as_view()),
    path('peekview/leave/', LeavePeekView.as_view()),
    path('offer-register/', live_offer_register_views, name='api_offer_register'),
    path('offer-register/<pk>', live_offer_register_details, name='api_offer_register_detail'),
    path('offer-register/check/', CheckLiveStreamRegistrationView.as_view(), name='api_offer_register_check'),
    # path('orders/', live_order_views, name='api_livestream_tracking'),
    # path('orders/<pk>', live_order_details, name='api_livestream_tracking_detail'),
]
