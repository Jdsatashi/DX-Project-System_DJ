from functools import partial

from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from account.handlers.validate_perm import ValidatePermRest
from marketing.price_list.api.serializers import PriceListSerializer
from marketing.price_list.models import PriceList
from utils.model_filter_paginate import filter_data


class GenericApiPriceList(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                          mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = PriceListSerializer
    queryset = PriceList.objects.all()
    # authentication_classes = [JWTAuthentication]
    # permission_classes = [partial(ValidatePermRest, model=PriceList)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['id', 'name', 'date_start', 'date_end'], *args,
                               **kwargs)
        return Response(response, status.HTTP_200_OK)
