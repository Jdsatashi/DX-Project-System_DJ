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


class ClientLV1(serializers.ModelSerializer):
    class Meta:
        model = ClientProfile
        fields = ['client_id', 'register_name']


class ClientProfileUserSerializer(serializers.ModelSerializer):
    client_group = ClientGroupView(source='client_group_id', read_only=True)
    nvtt = serializers.SerializerMethodField(read_only=True)
    client_lv1 = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ClientProfile
        fields = ['register_name', 'address', 'client_group_id', 'client_lv1', 'client_lv1_id', 'is_npp', 'client_group', 'nvtt', 'nvtt_id']
        extra_kwargs = {
            'is_npp': {'required': False},
        }

    def get_nvtt(self, obj):
        nvtt_id = obj.nvtt_id
        nvtt = User.objects.filter(id=nvtt_id).first()
        if nvtt is None:
            return None
        response = {
            'id': nvtt_id,
            'name': nvtt.employeeprofile.register_name
        }
        return response

    def get_client_lv1(self, obj):
        client_lv1_id = obj.client_lv1_id
        client_lv1 = ClientProfile.objects.filter(client_id_id=client_lv1_id).first()
        if client_lv1 is None:
            return None
        return {
            'id':  client_lv1_id,
            'name': client_lv1.register_name
        }


class ClientGroupSerializer(BaseRestrictSerializer):
    class Meta:
        model = ClientGroup
        fields = '__all__'
