from functools import partial

from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from account.handlers.validate_perm import ValidatePermRest
from marketing.order.api.serializers import OrderSerializer
from marketing.order.models import Order
from utils.model_filter_paginate import filter_data


class GenericApiOrder(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                          mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = OrderSerializer
    queryset = Order.objects.all()
    # authentication_classes = [JWTAuthentication]
    # permission_classes = [partial(ValidatePermRest, model=Order)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['id', 'date_get', 'date_company_get', 'client_id'], *args,
                               **kwargs)
        return Response(response, status.HTTP_200_OK)
