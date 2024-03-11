from django.contrib import admin
from django.urls import path, include

from .views import home


urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('draft/', include('draft.urls', 'draft')),
    path('khach-hang/', include('qlsx.khach_hang.urls', 'khach_hang'))
]
