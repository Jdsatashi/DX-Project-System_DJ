from django.urls import path
from rest_framework.routers import DefaultRouter

from user_system.employee_profile.api.views import GenericApiEmployee, GenericApiDepartment, GenericApiPosition

app_name = 'employee_profile'

router = DefaultRouter()
router.register('genericview', GenericApiEmployee, basename='api_employee')
router.register('genericview', GenericApiDepartment, basename='api_department')
router.register('genericview', GenericApiPosition, basename='api_position')

# Draft view
employees_view = GenericApiEmployee.as_view({'get': 'list', 'post': 'create'})
employee_detail_view = GenericApiEmployee.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})

departments_view = GenericApiDepartment.as_view({'get': 'list', 'post': 'create'})
department_detail_view = GenericApiDepartment.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})

positions_view = GenericApiPosition.as_view({'get': 'list', 'post': 'create'})
position_detail_view = GenericApiPosition.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})


urlpatterns = [
    path('profile/', employees_view),
    path('profile/<pk>', employee_detail_view),
    # path('departments/', departments_view),
    # path('departments/<pk>/', department_detail_view),
    # path('positions/', positions_view),
    # path('positions/<pk>/', position_detail_view),
]
