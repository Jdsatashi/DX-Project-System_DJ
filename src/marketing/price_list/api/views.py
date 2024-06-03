from functools import partial

from django.utils import timezone
from rest_framework import viewsets, mixins, status
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from account.handlers.perms import perm_queryset
from account.handlers.validate_perm import ValidatePermRest
from app.logs import app_log
from marketing.price_list.api.serializers import PriceListSerializer, SpecialOfferSerializer
from marketing.price_list.models import PriceList, SpecialOffer
from utils.model_filter_paginate import filter_data


class GenericApiPriceList(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                          mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = PriceListSerializer
    # queryset = PriceList.objects.all()
    authentication_classes = [JWTAuthentication, BasicAuthentication]

    permission_classes = [partial(ValidatePermRest, model=PriceList)]

    def get_queryset(self):
        app_log.info(f"Getting query set")
        return perm_queryset(self)

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['id', 'name', 'date_start', 'date_end'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)

    @action(methods=['get'], detail=False, url_path='now', url_name='now')
    def now(self, request, *args, **kwargs):
        today = timezone.localdate()
        queryset = self.get_queryset().filter(date_start__lte=today, date_end__gte=today)
        response = filter_data(self, request, ['id', 'name', 'date_start', 'date_end'], queryset=queryset,
                               **kwargs)
        return Response(response)


class ApiSpecialOffer(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                      mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = SpecialOfferSerializer
    # queryset = SpecialOffer.objects.all()
    authentication_classes = [JWTAuthentication, BasicAuthentication]
    permission_classes = [partial(ValidatePermRest, model=PriceList)]

    def get_queryset(self):
        return perm_queryset(self)

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['id', 'name', 'status', 'type_list'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)


class ApiSpecialOfferConsider(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = SpecialOfferSerializer
    queryset = SpecialOffer.objects.filter(type_list='consider_offer_user')
    authentication_classes = [JWTAuthentication, BasicAuthentication]
    # permission_classes = [partial(ValidatePermRest, model=PriceList)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['id', 'name', 'status'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)
