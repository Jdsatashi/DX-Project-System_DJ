from django.urls import path
from rest_framework.routers import DefaultRouter

from marketing.order.api.views import GenericApiOrder, ProductStatisticsView, OrderReportView, \
    ExportReport, TotalStatisticsView, ApiSeasonalStatistic, ApiSeasonalStatisticUser, OrderSOCount
from utils.constants import actions_views, actions_detail

app_name = "api_order"

router = DefaultRouter()
router.register('genericview', GenericApiOrder, basename='api_order')

order_views = GenericApiOrder.as_view(actions_views)
order_details = GenericApiOrder.as_view(actions_detail)

stats_users_views = ApiSeasonalStatisticUser.as_view(actions_views)
stats_users_details = ApiSeasonalStatisticUser.as_view(actions_detail)

stats_season_views = ApiSeasonalStatistic.as_view(actions_views)
stats_season_details = ApiSeasonalStatistic.as_view(actions_detail)


urlpatterns = [
    path('', order_views, name='api_order_view'),
    path('<pk>', order_details, name='api_order_detail'),
    path('self/', GenericApiOrder.as_view({'get': 'users_order'})),
    path('statistic/', ProductStatisticsView.as_view()),
    path('total-statistic/', TotalStatisticsView.as_view()),
    path('report/', OrderReportView.as_view(), name='order_report'),
    path('report/export/', ExportReport.as_view()),

    path('season-stats-users/', stats_users_views, name='api_stats_users_views'),
    path('season-stats-users/<pk>', stats_users_details, name='api_stats_users_details'),

    path('season-stats/', stats_season_views, name='api_stats_season_views'),
    path('season-stats/<pk>', stats_season_details, name='api_stats_season_details'),
    path('season-stats/<pk>/export', ApiSeasonalStatistic.as_view({'get': 'export'}), name='api_export_stats_season_details'),

    path('used-so/', OrderSOCount.as_view())
]
