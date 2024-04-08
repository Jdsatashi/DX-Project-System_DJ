from account.handlers.restrict_serializer import BaseRestrictSerializer
from user_system.client_group.models import ClientGroup


class ClientGroupSerializer(BaseRestrictSerializer):
    class Meta:
        model = ClientGroup
        fields = '__all__'
