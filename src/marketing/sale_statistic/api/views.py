from django.utils import timezone
from rest_framework import viewsets, mixins, status
from rest_framework.authentication import BasicAuthentication
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from account.models import User
from marketing.sale_statistic.api.serializers import SaleStatisticSerializer, SaleMonthTargetSerializer
from marketing.sale_statistic.models import SaleStatistic, SaleTarget
from utils.model_filter_paginate import filter_data


class ApiSaleStatistic(viewsets.GenericViewSet, mixins.ListModelMixin,
                       mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = SaleStatisticSerializer
    queryset = SaleStatistic.objects.all()
    authentication_classes = [JWTAuthentication, BasicAuthentication]

    # permission_classes = [partial(ValidatePermRest, model=SaleStatistic)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['user'],
                               **kwargs)
        return Response(response, status=status.HTTP_200_OK)


class CurrentMonthSaleStatisticView(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = SaleStatisticSerializer
    authentication_classes = [JWTAuthentication, BasicAuthentication]

    # permission_classes = [partial(ValidatePermRest, model=SaleTarget)]

    def get_queryset(self):
        today = timezone.now().date()
        first_day_of_month = today.replace(day=1)
        return SaleStatistic.objects.filter(month=first_day_of_month)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        response = filter_data(self, request, ['user__id'], queryset=queryset,
                               **kwargs)
        return Response(response, status=status.HTTP_200_OK)


class UserMonthSaleStatisticView(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = SaleStatisticSerializer
    authentication_classes = [JWTAuthentication, BasicAuthentication]

    # permission_classes = [partial(ValidatePermRest, model=SaleTarget)]

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        user = User.objects.get(id=user_id)

        return SaleStatistic.objects.filter(user=user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        response = filter_data(self, request, ['month'], queryset=queryset,
                               **kwargs)
        return Response(response, status=status.HTTP_200_OK)


class ApiSaleMonthTarget(viewsets.GenericViewSet, mixins.ListModelMixin,
                         mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = SaleMonthTargetSerializer
    queryset = SaleTarget.objects.all()
    authentication_classes = [JWTAuthentication, BasicAuthentication]

    # permission_classes = [partial(ValidatePermRest, model=SaleTarget)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['month'],
                               **kwargs)
        return Response(response, status=status.HTTP_200_OK)
