from django.urls import path
from rest_framework.routers import DefaultRouter

from marketing.sale_statistic.api.views import ApiSaleStatistic, ApiSaleMonthTarget, CurrentMonthSaleStatisticView
from utils.constants import actions_detail

app_name = 'api_sale_statistic'

router = DefaultRouter()

router.register('genericview', ApiSaleStatistic, basename='api_sale_statistic')
router.register('genericview', ApiSaleMonthTarget, basename='api_sale_month_target')

view_sale_statistic = ApiSaleStatistic.as_view(actions={'get': 'list'})
detail_sale_statistic = ApiSaleStatistic.as_view(actions=actions_detail)

view_sale_month_target = ApiSaleMonthTarget.as_view(actions={'get': 'list'})
detail_sale_month_target = ApiSaleMonthTarget.as_view(actions=actions_detail)

urlpatterns = [
    path('', view_sale_statistic, name='api_sale_statistic'),
    path('<pk>', detail_sale_statistic, name='api_sale_statistic'),
    path('now/', CurrentMonthSaleStatisticView.as_view({'get': 'list'}), name='api_sale_statistic_now'),
    path('month-target/', view_sale_month_target, name='api_sale_month_target'),
    path('month-target/<pk>', detail_sale_month_target, name='api_sale_month_target'),
]