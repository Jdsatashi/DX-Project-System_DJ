from .forms import CreateGroupDraftForm, CreateDraftForm
from .models import GroupDraft, Draft


def handle_create_group_draft(request):
    context = {}
    groups = GroupDraft.objects.all()
    form = CreateGroupDraftForm(request.POST or None)
    if form.is_valid():
        obj = form.save(commit=False)
        form.clean()
        obj.save()
    context['form'] = form
    context['groups'] = groups
    return context


def handle_get_list_draft(request):
    context = {}
    drafts = Draft.objects.all()
    context['drafts'] = drafts
    return context


def handle_create_draft(request):
    context = {}
    form = CreateDraftForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return "direct"
    context['form'] = form
    return context


def handle_draft_id(request, id):
    context = {}
    # draft = get_object_or_404(Draft, id=id)
    # draft = Draft.objects.filter(id=id).first()
    draft = Draft.objects.get(id=id)
    form = CreateDraftForm(request.POST or None, instance=draft)
    if request.method == 'POST':
        if form.is_valid():
            obj = form.save(commit=False)
            obj.save()
            return "direct"
    context['form'] = form
    context['draft'] = draft
    return context


def handle_delete_draft(request, id):
    draft = Draft.objects.get(id=id)
    if draft is None:
        return False
    if request.method == 'POST':
        draft.delete()
    return True
