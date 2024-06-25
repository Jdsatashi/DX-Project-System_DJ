from django.db import transaction
from rest_framework import serializers

from marketing.medias.models import Banner, BannerItem


class BannerItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BannerItem
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class BannerItemWrite(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = BannerItem
        exclude = ['id', 'created_at']

    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None


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
