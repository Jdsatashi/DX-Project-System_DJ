from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.shortcuts import render
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView

schema_view = SpectacularAPIView.as_view()


# Create homepage view
def home(request):
    return render(request, 'homepage.html')


urlpatterns = [
    path('', home, name='home'),
    path('system/admin/', admin.site.urls),
    path('accounts/', include('account.urls', 'account')),
    path('api/schema/', schema_view, name='api-schema'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='api-schema'), name='redoc'),
    path('application/api/v1/2024/', include('app.api_routes.routes', 'api_routes')),
]

# Add static files tto url
urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
