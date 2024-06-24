from rest_framework import viewsets, mixins, status
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from marketing.medias.api.banner.serializers import BannerSerializer, BannerItemSerializer
from marketing.medias.models import Banner, BannerItem
from utils.model_filter_paginate import filter_data


class ApiBanner(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                 mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = BannerSerializer
    queryset = Banner.objects.all()

    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]
    # permission_classes = [partial(ValidatePermRest, model=Banner)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['id', 'name'], **kwargs)
        return Response(response, status.HTTP_200_OK)


class ApiBannerItem(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                    mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = BannerItemSerializer
    queryset = BannerItem.objects.all()

    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]
    # permission_classes = [partial(ValidatePermRest, model=BannerItem)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['id', 'name'], **kwargs)
        return Response(response, status.HTTP_200_OK)
