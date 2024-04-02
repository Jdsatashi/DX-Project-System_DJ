from functools import partial

from rest_framework import mixins, viewsets
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from account.handlers.validate_quyen import ValidateQuyenRest
from draft.api.serializers import DraftSerializer, GroupDraftSerializer
from draft.models import Draft, GroupDraft


class GenericDraft(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = DraftSerializer
    queryset = Draft.objects.all()
    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]
    permission_classes = [partial(ValidateQuyenRest, model=Draft)]


class GenericGroupDraft(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                        mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = GroupDraftSerializer
    queryset = GroupDraft.objects.all()
    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]
    permission_classes = [partial(ValidateQuyenRest, model=GroupDraft)]


@api_view(['GET', 'POST'])
def DraftWithPermission(request):
    if request.method == 'GET':
        list_draft = Draft.objects.all()
        serializer = DraftSerializer(list_draft, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = DraftSerializer(data=request.data)
