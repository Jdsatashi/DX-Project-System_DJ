from rest_framework import serializers

from account.handlers.restrict_serializer import BaseRestrictSerializer
from marketing.sale_statistic.models import SaleStatistic, SaleTarget


class SaleStatisticSerializer(BaseRestrictSerializer):
    class Meta:
        model = SaleStatistic
        fields = '__all__'
        read_only_fields = ('id', 'user', 'month', 'total_turnover', 'used_turnover', 'available_turnover')


class SaleMonthTargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleTarget
        fields = ('id', 'month')
