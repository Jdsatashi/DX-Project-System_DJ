from django.db import transaction
from rest_framework import serializers

from app import settings
from app.logs import app_log
from marketing.medias.models import Banner, BannerItem
from system.file_upload.api.serializers import FileShortViewSerializer
from utils.env import APP_SERVER


class BannerItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BannerItem
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class BannerItemWrite(serializers.ModelSerializer):
    class Meta:
        model = BannerItem
        exclude = ['id', 'created_at']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if request:
            app_log.info(f"In request")
            representation['file_url'] = request.build_absolute_uri(instance.file.file.url)
        else:
            representation['file_url'] = APP_SERVER + instance.file.file.url if instance.file else None
        return representation




class BannerSerializer(serializers.ModelSerializer):
    banner_items = BannerItemWrite(many=True, required=False)

    class Meta:
        model = Banner
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')

    def create(self, validated_data):
        banner_items_data = validated_data.pop('banner_items', [])
        with transaction.atomic():
            banner = Banner.objects.create(**validated_data)
            for banner_item_data in banner_items_data:
                BannerItem.objects.create(banner=banner, **banner_item_data)
            return banner

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance.banner_items.all().delete()
            banner_items_data = validated_data.pop('banner_items')
            instance.update(**validated_data)
            for banner_item_data in banner_items_data:
                BannerItem.objects.create(banner=instance, **banner_item_data)
            return instance
