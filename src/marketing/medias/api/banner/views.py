from django.db.models import Q
from rest_framework import viewsets, mixins, status
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from app.logs import app_log
from marketing.medias.api.banner.serializers import BannerSerializer, BannerItemSerializer
from marketing.medias.models import Banner, BannerItem
from utils.model_filter_paginate import filter_data


class ApiBanner(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = BannerSerializer
    queryset = Banner.objects.all()

    # authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]
    # permission_classes = [partial(ValidatePermRest, model=Banner)]

    def get_authenticators(self):
        try:
            if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                self.authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]
            else:
                self.authentication_classes = []
        except AttributeError:
            self.authentication_classes = []
            return super().get_authenticators()
        return super().get_authenticators()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # Get query params
        banner_type = request.query_params.get('type', None)
        display_type = request.query_params.get('display_type', None)
        # Get strict as boolean
        strict = request.data.get('strict') or request.query_params.get('strict', 0)
        strict = int(strict)
        strict = strict if strict in [0, 1] else 0
        strict_mode = bool(strict)

        query_filter = Q()
        query_type = '__exact' if strict_mode else '__icontains'

        if banner_type:
            query_filter &= Q(**{f'type{query_type}': banner_type})

        if display_type:
            query_filter &= Q(**{f'display_type{query_type}': display_type})

        queryset = queryset.filter(query_filter)

        response = filter_data(self, request, ['id', 'name'], queryset=queryset, **kwargs)
        return Response(response, status.HTTP_200_OK)

    # def get_permissions(self):
    #     if self.action in ['create', 'update', 'partial_update', 'destroy']:
    #         self.permission_classes = [partial(ValidatePermRest, model=Banner)]
    #     else:
    #         self.permission_classes = []
    #     return super().get_permissions()


class ApiBannerItem(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                    mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = BannerItemSerializer
    queryset = BannerItem.objects.all()

    # authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]
    # permission_classes = [partial(ValidatePermRest, model=BannerItem)]

    def get_authenticators(self):
        try:
            if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                self.authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]
            else:
                self.authentication_classes = []
        except AttributeError:
            self.authentication_classes = []
            return super().get_authenticators()
        return super().get_authenticators()

    # def get_permissions(self):
    #     if self.action in ['create', 'update', 'partial_update', 'destroy']:
    #         self.permission_classes = [partial(ValidatePermRest, model=Banner)]
    #     else:
    #         self.permission_classes = []
    #     return super().get_permissions()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # Get query params
        banner_type = request.query_params.get('type', None)
        display_type = request.query_params.get('display_type', None)
        # Get strict as boolean
        strict = request.data.get('strict') or request.query_params.get('strict', 0)
        strict = int(strict)
        strict = strict if strict in [0, 1] else 0
        strict_mode = bool(strict)

        query_filter = Q()
        query_type = '__exact' if strict_mode else '__icontains'

        if banner_type:
            query_filter &= Q(**{f'banner__type{query_type}': banner_type})

        if display_type:
            query_filter &= Q(**{f'banner__display_type{query_type}': display_type})
        app_log.info(f"TEST: {query_filter}")
        queryset = queryset.filter(query_filter)

        response = filter_data(self, request, ['id', 'title', 'note', 'banner__id', 'banner__name'], queryset=queryset, **kwargs)
        return Response(response, status.HTTP_200_OK)
