from account.handlers.restrict_serializer import BaseRestrictSerializer
from user_system.client_profile.models import ClientProfile


class ClientProfileSerializer(BaseRestrictSerializer):
    class Meta:
        model = ClientProfile
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at']
