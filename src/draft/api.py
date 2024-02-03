from django.http import HttpResponse

from .handle import handle_create_group_draft, handle_get_list_draft, handle_create_draft
from __init__.app_log import logger


def api_create_group_draft(request):
    context = handle_create_group_draft(request)
    return HttpResponse(context, content_type='application/json')


def api_list_draft(request):
    context = handle_get_list_draft(request)
    drafts = list(context['drafts'].values())
    logger.info(f"Data: {drafts}")
    return HttpResponse(drafts, content_type='application/json')
