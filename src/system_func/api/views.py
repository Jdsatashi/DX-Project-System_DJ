from functools import partial

from rest_framework import viewsets, mixins, status
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from account.handlers.validate_perm import ValidatePermRest
from system_func.api.serializers import PeriodSeasonSerializer, SystemConfigSerializer
from system_func.models import PeriodSeason, SystemConfig
from utils.model_filter_paginate import filter_data


class ApiPeriodSeason(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                      mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = PeriodSeasonSerializer
    queryset = PeriodSeason.objects.all()
    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]
    permission_classes = [partial(ValidatePermRest, model=PeriodSeason)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['type', 'period'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)


class ApiSystemConfig(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                      mixins.RetrieveModelMixin, mixins.UpdateModelMixin):
    serializer_class = SystemConfigSerializer
    queryset = SystemConfig.objects.all()
    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_authenticators(self):
        if self.request.method == 'GET':
            return []
        return super().get_authenticators()

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['name', 'id'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)
