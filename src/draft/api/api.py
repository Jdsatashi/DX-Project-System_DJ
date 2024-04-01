from functools import partial

from rest_framework import mixins, viewsets
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from account.validate_quyen import ValidateQuyenRest
from draft.api.serializers import DraftSerializer, GroupDraftSerializer
from draft.models import Draft, GroupDraft


class GenericDraft(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = DraftSerializer
    queryset = Draft.objects.all()
    draft_perm = ValidateQuyenRest(model_name="Draft")
    # authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]
    permission_classes = [partial(ValidateQuyenRest, model_name="Draft")]


class GenericGroupDraft(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                        mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = GroupDraftSerializer
    queryset = GroupDraft.objects.all()
    group_draft_perm = ValidateQuyenRest(model_name="GroupDraft")
    # authentication_classes = [TokenAuthentication]
    permission_classes = [partial(ValidateQuyenRest, model_name="GroupDraft")]
