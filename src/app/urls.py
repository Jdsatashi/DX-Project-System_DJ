from django.contrib import admin
from django.shortcuts import render
from django.urls import path, include
from rest_framework.schemas import get_schema_view


# Create homepage view
def home(request):
    return render(request, 'homepage.html')


urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('draft/', include('draft.urls', 'draft')),
    path('accounts/', include('account.urls', 'account')),
    path('api_schema', get_schema_view(title='API schema', description='Guide for REST Api'), name='api_schema'),
    path('application/api/v1/2024/', include('app.api_routes.routes', 'api_routes')),
]
