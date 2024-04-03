from django.urls import path

from .views import *

app_name = 'draft'

urlpatterns = [
    path('', list_draft, name='list_draft'),
    path('group/create', create_group_draft, name='create_group_draft'),
    path('create', create_draft, name='create_draft'),
    path('detail/<pk>', draft_item, name='draft_item'),
    path('detail/<pk>/delete', draft_delete, name='draft_delete'),
]
