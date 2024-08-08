from rest_framework import serializers

from system_func.models import PeriodSeason


class PeriodSeasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeriodSeason
        fields = '__all__'
