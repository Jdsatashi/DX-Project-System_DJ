from rest_framework import serializers

from account.handlers.restrict_serializer import BaseRestrictSerializer
from user_system.client_profile.models import ClientProfile


class ClientProfileSerializer(BaseRestrictSerializer):
    class Meta:
        model = ClientProfile
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at']


class ClientProfileUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientProfile
        fields = ['register_name', 'address', 'client_group_id', 'is_npp', 'nvtt_id']
        extra_kwargs = {
            'is_npp': {'required': False},
        }
