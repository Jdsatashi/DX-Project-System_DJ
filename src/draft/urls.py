from django.urls import path
from .views import *

app_name = 'draft'

urlpatterns = [
    path('', list_draft, name='list_draft'),
    path('group/create', create_group_draft, name='create_group_draft')
]
