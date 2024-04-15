from rest_framework import serializers

from account.handlers.restrict_serializer import BaseRestrictSerializer
from draft.models import Draft, GroupDraft


class DraftSerializer(BaseRestrictSerializer):
    class Meta:
        model = Draft
        fields = '__all__'

    def create(self, validated_data):
        # Split to data for save and quyen data for add quyen
        data, quyen_data = self.split_data(validated_data)
        # restrict check if create request required quyen
        restrict = quyen_data.get('restrict')
        # Creating data
        instance = super().create(data)
        # When required quyen, handle to add quyen
        if restrict:
            self.handle_restrict(quyen_data, instance.id, self.Meta.model)
        return instance

    def update(self, instance, validated_data):
        # Split to data for save and quyen data for add quyen
        data, quyen_data = self.split_data(validated_data)
        group_data = validated_data.pop('group', None)
        # restrict check if create request required quyen
        restrict = quyen_data.get('restrict')

        for attr, value in data.items():
            setattr(instance, attr, value)
        if group_data is not None:
            instance.group.set(group_data)
        instance.save()

        if restrict:
            self.handle_restrict(quyen_data, instance.id, self.Meta.model)
        return instance


class GroupDraftSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupDraft
        fields = '__all__'
