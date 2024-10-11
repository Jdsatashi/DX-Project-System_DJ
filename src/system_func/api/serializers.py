from rest_framework import serializers

from system_func.models import PeriodSeason, SystemConfig


class PeriodSeasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeriodSeason
        fields = '__all__'


class SystemConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemConfig
        fields = '__all__'
        extra_kwargs = {
            'name': {'required': True, 'allow_null': False, 'allow_blank': False},
            'value': {'required': True, 'allow_blank': True},
            'note': {'required': False, 'allow_blank': True},
        }
