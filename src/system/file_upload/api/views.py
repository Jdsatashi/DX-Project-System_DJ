from functools import partial

from rest_framework import viewsets, mixins
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication

from account.handlers.validate_perm import ValidatePermRest
from system.file_upload.api.serializers import FileUploadSerializer, ContentFileSerialier, FileProductSerializer, \
    FileProductCateSerializer
from system.file_upload.models import FileUpload, ContentFile, ProductCateFile, ProductFile


class GenericApiFileUpload(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                           mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = FileUploadSerializer
    queryset = FileUpload.objects.all()
    authentication_classes = [JWTAuthentication, BasicAuthentication]
    # permission_classes = [partial(ValidatePermRest, model=FileUpload)]


class GenericApiFileContent(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                            mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = ContentFileSerialier
    queryset = ContentFile.objects.all()


class ApiFileProductCate(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                         mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = FileProductCateSerializer
    queryset = ProductCateFile.objects.all()
    authentication_classes = [JWTAuthentication, BasicAuthentication]
    # permission_classes = [partial(ValidatePermRest, model=ProductCateFile)]


class ApiFileProduct(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = FileProductSerializer
    queryset = ProductFile.objects.all()
    authentication_classes = [JWTAuthentication, BasicAuthentication]
    # permission_classes = [partial(ValidatePermRest, model=ProductFile)]
