from django.urls import path

from marketing.medias.api.banner.views import ApiBanner, ApiBannerItem
from utils.constants import actions_views, actions_detail

app_name = 'banner_api'


banner_views = ApiBanner.as_view(actions_views)
banner_details = ApiBanner.as_view(actions_detail)

item_views = ApiBannerItem.as_view(actions_views)
item_details = ApiBannerItem.as_view(actions_detail)

urlpatterns = [
    path('', banner_views),
    path('<pk>', banner_details),
    path('item/', item_views),
    path('item/<pk>', item_details),
]
