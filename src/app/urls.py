from django.contrib import admin
from django.shortcuts import render
from django.urls import path, include


# Create homepage view
def home(request):
    return render(request, 'homepage.html')


urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('draft/', include('draft.urls', 'draft')),
    path('accounts/', include('account.urls', 'account')),
    path('application/api/v1/2024/', include('app.api_routes.routes', 'api_routes')),
]
