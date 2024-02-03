from django import forms
from .models import Draft, GroupDraft


class CreateDraftForm(forms.ModelForm):
    class Meta:
        model = Draft
        fields = ['title', 'content', 'purpose', 'no', 'group']

    def __init__(self, *args, **kwargs):
        super(CreateDraftForm, self).__init__(*args, **kwargs)
        self.fields['group'].empty_label = 'Select a group'


class CreateGroupDraftForm(forms.ModelForm):
    class Meta:
        model = GroupDraft
        fields = ['name', 'level']
