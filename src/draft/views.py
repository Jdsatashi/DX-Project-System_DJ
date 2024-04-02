from django.shortcuts import render, redirect

from account.handlers.validate_quyen import quyen
# Create your views here.
from draft.handlers.handle import handle_create_group_draft, handle_get_list_draft, handle_create_draft, handle_draft_id, \
    handle_delete_draft
from draft.models import GroupDraft

# draft_content = ContentType.objects.get_for_model(Draft)
# draft_group_content = ContentType.objects.get_for_model(GroupDraft)

# draft_name = f"{draft_content.app_label}_{draft_content.model}"
# draft_group_name = f"{draft_group_content.app_label}_{draft_group_content.model}"
draft_group_name = ""


@quyen(GroupDraft, 'create')
def create_group_draft(request):
    context = handle_create_group_draft(request)
    return render(request, 'draft/group/create.html', context)
    # return HttpResponse(context)


def list_draft(request):
    context = handle_get_list_draft(request)
    return render(request, 'draft/index.html', context)


def create_draft(request):
    context = handle_create_draft(request)
    if context == "direct":
        return redirect("draft:list_draft")
    return render(request, "draft/create.html", context)


def draft_item(request, id):
    context = handle_draft_id(request, id)
    if context == "direct":
        return redirect("draft:draft_item", id=id)
    return render(request, "draft/show.html", context)


def draft_delete(request, id):
    is_deleted = handle_delete_draft(request, id)
    if is_deleted:
        return redirect("draft:list_draft")
    else:
        return redirect("draft:draft_item", id=id)
