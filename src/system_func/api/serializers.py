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
