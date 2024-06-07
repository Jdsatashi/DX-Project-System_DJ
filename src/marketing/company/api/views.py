from functools import partial

from rest_framework import viewsets, mixins, status
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from account.handlers.validate_perm import ValidatePermRest
from marketing.company.api.serializers import CompanySerializer
from marketing.company.models import Company
from utils.model_filter_paginate import filter_data


class ApiCompany(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                 mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = CompanySerializer
    queryset = Company.objects.all()
    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]

    permission_classes = [partial(ValidatePermRest, model=Company)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['id', 'name'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)
