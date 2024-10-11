from django.urls import path

from system_func.api.views import ApiPeriodSeason, ApiSystemConfig
from utils.constants import actions_detail, actions_views

app_name = 'system_func'

period_season_views = ApiPeriodSeason.as_view(actions_views)
period_season_details = ApiPeriodSeason.as_view(actions_detail)

system_conf_views = ApiSystemConfig.as_view(actions_views)
system_conf_details = ApiSystemConfig.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update'})

urlpatterns = [
    path('', system_conf_views),
    path('<pk>', system_conf_details),

    path('period/', period_season_views, name='api_period_season_views'),
    path('period/<pk>', period_season_details, name='api_period_season_details'),
]
