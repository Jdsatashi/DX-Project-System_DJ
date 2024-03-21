from django.urls import path

from old_data.views import insertDB

urlpatterns = [
    path('insert-data/', insertDB, name='insertDB')
]
