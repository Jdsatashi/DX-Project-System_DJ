from django.shortcuts import render
from .forms import *
# Create your views here.


def create_group_draft(request):
    context = {}
    groups = GroupDraft.objects.all()
    form = CreateGroupDraftForm(request.POST or None)
    if form.is_valid():
        obj = form.save(commit=False)
        form.clean()
        obj.save()
    context['form'] = form
    context['groups'] = groups
    return render(request, 'draft/group/create.html', context)


def list_draft(request):
    context = {}
    return render(request, 'draft/index.html', context)


def create_draft(request):
    form = CreateDraftForm()
    if request.method == 'POST':
        title = request.POST['title']
        content = request.POST['content']
        purpose = request.POST['purpose']
        no = request.POST['no']
        group = request.POST['group']
