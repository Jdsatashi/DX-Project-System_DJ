from rest_framework import serializers

from account.handlers.restrict_serializer import BaseRestrictSerializer
from account.models import User
from user_system.client_profile.models import ClientProfile, ClientGroup


class ClientProfileSerializer(BaseRestrictSerializer):
    class Meta:
        model = ClientProfile
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at']


class ClientGroupView(serializers.ModelSerializer):
    class Meta:
        model = ClientGroup
        fields = ['id', 'name']


class ClientProfileUserSerializer(serializers.ModelSerializer):
    client_group_id = ClientGroupView(read_only=True)
    nvtt_id = serializers.SerializerMethodField()

    class Meta:
        model = ClientProfile
        fields = ['register_name', 'address', 'client_group_id', 'is_npp', 'nvtt_id']
        extra_kwargs = {
            'is_npp': {'required': False},
        }

    def get_nvtt_id(self, obj):
        nvtt_id = obj.nvtt_id
        nvtt = User.objects.filter(id=nvtt_id).first()
        if nvtt is None:
            return None
        response = {
            'id': nvtt_id,
            'name': nvtt.employeeprofile.register_name
        }
        return response


class ClientGroupSerializer(BaseRestrictSerializer):
    class Meta:
        model = ClientGroup
        fields = '__all__'
