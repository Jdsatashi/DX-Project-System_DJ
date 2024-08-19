from django.db import transaction
from django.db.models import Sum
from rest_framework import serializers

from account.handlers.restrict_serializer import BaseRestrictSerializer
from marketing.order.models import OrderDetail
from marketing.sale_statistic.models import SaleStatistic, SaleTarget, UserSaleStatistic, UsedTurnover


class SaleStatisticSerializer(BaseRestrictSerializer):
    class Meta:
        model = SaleStatistic
        fields = '__all__'
        read_only_fields = ('id', 'user', 'month', 'total_turnover', 'used_turnover', 'available_turnover')


class SaleMonthTargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleTarget
        fields = '__all__'


class UserSaleStatisticSerializer(serializers.ModelSerializer):
    fix_turnover = serializers.IntegerField(write_only=True, allow_null=True, required=False)
    is_bonus = serializers.BooleanField(write_only=True, default=True)
    note = serializers.CharField(write_only=True, allow_null=True, required=False)
    import_file = serializers.FileField(required=False, write_only=True, allow_null=True)

    class Meta:
        model = UserSaleStatistic
        fields = '__all__'
        read_only_fields = ('id', 'user', 'turnover', 'created_at', 'updated_at')

    def to_representation(self, instance: UserSaleStatistic):
        representation = super().to_representation(instance)
        user = instance.user

        

        user_so = user.order_set.filter(is_so=True).exclude(new_special_offer__type_list='consider_offer_user')
        used_box = OrderDetail.objects.filter(order_id__in=user_so).aggregate(total_box=Sum('order_box'))
        representation['used_box'] = used_box['total_box']
        return representation

    def update(self, instance: UserSaleStatistic, validated_data):
        fix_turnover = validated_data.get('fix_turnover', None)
        is_bonus: bool = validated_data.get('is_bonus')
        note = validated_data.get('note', None)
        if not fix_turnover:
            raise serializers.ValidationError({'message': 'input fix turnover fields'})
        with transaction.atomic():
            if is_bonus:
                fix_turnover = abs(fix_turnover)
            else:
                fix_turnover = -abs(fix_turnover)

            instance.turnover += fix_turnover
            UsedTurnover.objects.create(user_sale_stats=instance, purpose='admin_fix', turnover=fix_turnover, note=note)

            instance.save()
            return instance


class UserUsedStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsedTurnover
        fields = '__all__'
