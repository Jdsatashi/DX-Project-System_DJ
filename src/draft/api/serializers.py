from rest_framework import serializers

from draft.models import Draft, GroupDraft


class DraftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Draft
        fields = '__all__'


class GroupDraftSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupDraft
        fields = '__all__'
