from functools import partial

from rest_framework import viewsets, mixins, status
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from account.handlers.validate_perm import ValidatePermRest
from system.file_upload.api.serializers import FileUploadSerializer, ContentFileSerialier, FileProductSerializer, \
    FileProductCateSerializer
from system.file_upload.models import FileUpload, ContentFile, ProductCateFile, ProductFile
from utils.model_filter_paginate import filter_data


class GenericApiFileUpload(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                           mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = FileUploadSerializer
    queryset = FileUpload.objects.all()
    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]
    permission_classes = [partial(ValidatePermRest, model=FileUpload)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['name', 'type', 'note'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)


class GenericApiFileContent(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                            mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = ContentFileSerialier
    queryset = ContentFile.objects.all()

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['id'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)


class ApiFileProductCate(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                         mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = FileProductCateSerializer
    queryset = ProductCateFile.objects.all()
    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]
    # permission_classes = [partial(ValidatePermRest, model=ProductCateFile)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['id'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)


class ApiFileProduct(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = FileProductSerializer
    queryset = ProductFile.objects.all()
    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]
    # permission_classes = [partial(ValidatePermRest, model=ProductFile)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['id'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)
