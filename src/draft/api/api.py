from rest_framework import mixins, viewsets
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from draft.api.serializers import DraftSerializer, GroupDraftSerializer
from draft.models import Draft, GroupDraft


class GenericDraft(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = DraftSerializer
    queryset = Draft.objects.all()
    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]


class GenericGroupDraft(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                        mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = GroupDraftSerializer
    queryset = GroupDraft.objects.all()
    # authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]
