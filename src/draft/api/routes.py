from django.urls import path
from rest_framework.routers import DefaultRouter

from draft.api.api import GenericDraft, GenericGroupDraft

app_name = 'api_draft'
router = DefaultRouter()
router.register('genericview', GenericDraft, basename='draft')
router.register('genericview', GenericGroupDraft, basename='groupDraft')

draft_view = GenericDraft.as_view({'get': 'list', 'post': 'create'})
draft_detail = GenericDraft.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'})
group_draft_list_view = GenericGroupDraft.as_view({'get': 'list', 'post': 'create'})
group_draft_detail_view = GenericGroupDraft.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'})


urlpatterns = [
    path('generic/', draft_view),
    path('generic/<pk>/', draft_view),
    path('group/generic/', group_draft_list_view),
    path('group/generic/<pk>/', group_draft_detail_view)
]