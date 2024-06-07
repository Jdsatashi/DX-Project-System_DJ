from django.urls import path
from rest_framework.routers import DefaultRouter

from marketing.company.api.views import ApiCompany
from utils.constants import actions_views, actions_detail

app_name = "api_company"

router = DefaultRouter()
router.register('genericview', ApiCompany, basename='api_company')

company_views = ApiCompany.as_view(actions_views)
company_details = ApiCompany.as_view(actions_detail)


urlpatterns = [
    path('', company_views, name='api_company_view'),
    path('<pk>', company_details, name='api_company_detail'),
]
