from functools import partial

from rest_framework import viewsets, mixins
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication

from account.handlers.validate_perm import ValidatePermRest
from system.file_upload.api.serializers import FileUploadSerializer, ContentFileSerialier
from system.file_upload.models import FileUpload, ContentFile


class GenericApiFileUpload(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                           mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = FileUploadSerializer
    queryset = FileUpload.objects.all()
    # authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]
    # permission_classes = [partial(ValidatePermRest, model=FileUpload)]


class GenericApiFileContent(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                            mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = ContentFileSerialier
    queryset = ContentFile.objects.all()
