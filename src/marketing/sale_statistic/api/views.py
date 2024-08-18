from functools import partial

import pandas as pd
from django.utils import timezone
from rest_framework import viewsets, mixins, status
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from account.handlers.validate_perm import ValidatePermRest
from account.models import User
from app.logs import app_log
from marketing.sale_statistic.api.serializers import SaleStatisticSerializer, SaleMonthTargetSerializer, \
    UserSaleStatisticSerializer, UserUsedStatsSerializer
from marketing.sale_statistic.models import SaleStatistic, SaleTarget, UserSaleStatistic, UsedTurnover
from utils.helpers import local_time
from utils.model_filter_paginate import filter_data


class ApiSaleStatistic(viewsets.GenericViewSet, mixins.ListModelMixin,
                       mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = SaleStatisticSerializer
    queryset = SaleStatistic.objects.all()
    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]
    permission_classes = [partial(ValidatePermRest, model=SaleStatistic)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['user__id'],
                               **kwargs)
        return Response(response, status=status.HTTP_200_OK)


class CurrentMonthSaleStatisticView(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = SaleStatisticSerializer
    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]
    permission_classes = [partial(ValidatePermRest, model=SaleTarget)]

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
    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]
    permission_classes = [partial(ValidatePermRest, model=SaleTarget)]

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
    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]
    permission_classes = [partial(ValidatePermRest, model=SaleTarget)]

    def list(self, request, *args, **kwargs):
        today = local_time().date()
        sale_target, _ = SaleTarget.objects.get_or_create(month=today)
        app_log.info(f"{sale_target}")
        response = filter_data(self, request, ['month'],
                               **kwargs)
        return Response(response, status=status.HTTP_200_OK)


class ApiMainSaleStatistic(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin):
    serializer_class = UserSaleStatisticSerializer
    queryset = UserSaleStatistic.objects.all()
    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]
    permission_classes = [partial(ValidatePermRest, model=UserSaleStatistic)]

    def list(self, request, *args, **kwargs):

        response = filter_data(self, request, ['user__id', 'user__username'],
                               **kwargs)
        return Response(response, status=status.HTTP_200_OK)

    def import_file(self, request, *args, **kwargs):
        file = request.data.get('import_file', None)
        if file is None:
            return Response({'message': 'import_file is required'})
        try:
            df = pd.read_excel(file, engine='openpyxl')

            if 'maKH' not in df.columns or 'thay_doi_doanh_so' not in df.columns:
                return Response({'message': 'File phải chứa các cột "maKH" và "thay_doi_doanh_so"'})

            data = df[['maKH', 'thay_doi_doanh_so']]
            update_turnover = list()
            for index, row in data.iterrows():
                user_id = row['maKH']
                fix_turnover = row['thay_doi_doanh_so']
                user_stats = UserSaleStatistic.objects.filter(user=user_id).first()
                if user_stats is None:
                    user_stats = UserSaleStatistic.objects.create(user=user_id)
                user_stats.turnover += fix_turnover
                update_turnover.append(user_stats)
            UserSaleStatistic.objects.bulk_update(update_turnover, ['turnover'])
            return Response({'message': 'Import file successfully'})

        except Exception as e:
            raise e


class ApiUserUsedStatistic(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = UserUsedStatsSerializer
    queryset = UsedTurnover.objects.all()
    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]
    permission_classes = [partial(ValidatePermRest, model=UsedTurnover)]

    def list(self, request, *args, **kwargs):

        response = filter_data(self, request, ['user_sale_stats__user__id', 'user_sale_stats__user__username'],
                               **kwargs)
        return Response(response, status=status.HTTP_200_OK)
