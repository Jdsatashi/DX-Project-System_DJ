from rest_framework import viewsets, mixins

from user_system.client_profile.api.serializers import ClientGroupSerializer
from user_system.client_profile.models import ClientGroup


class GenericApiClientGroup(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                            mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = ClientGroupSerializer
    queryset = ClientGroup.objects.all()
    # authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]
    # permission_classes = [partial(ValidatePermRest, model=ClientGroup)]
