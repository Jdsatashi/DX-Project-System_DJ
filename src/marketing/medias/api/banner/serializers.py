from django.db import transaction
from rest_framework import serializers

from app import settings
from app.logs import app_log
from marketing.medias.models import Banner, BannerItem, BannerDisplay
from system.file_upload.api.serializers import FileShortViewSerializer
from system.file_upload.models import FileUpload
from utils.env import APP_SERVER


class BannerItemSerializer(serializers.ModelSerializer):
    file_upload = serializers.FileField(allow_null=True, write_only=True, required=False)

    class Meta:
        model = BannerItem
        fields = '__all__'
        read_only_fields = ('id', 'created_at')
        extra_kwargs = {
            'file': {'write_only': True},
            'video_url': {'required': False}
        }

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        try:
            representation['file_url'] = APP_SERVER + instance.file.file.url if instance.file else None
        except AttributeError:
            pass
        return representation

    def create(self, validated_data):
        file_upload_data = validated_data.pop('file_upload', None)
        file_instance = validated_data.get('file', None)
        banner = validated_data.get('banner')
        if banner:
            display_type = banner.display_type
            if display_type == BannerDisplay.VIDEO:
                video_url = validated_data.get('video_url', None)
                if video_url is None:
                    raise serializers.ValidationError("Video_url is required.")

        elif not file_instance and not file_upload_data:
            raise serializers.ValidationError("File or file_upload is required.")

        with transaction.atomic():
            if file_instance is None and file_upload_data:
                file_instance = FileUpload.objects.create(file=file_upload_data)
            app_log.info(f"Test file: {file_instance}")
            validated_data['file'] = file_instance

            banner_item = BannerItem.objects.create(**validated_data)
            return banner_item

    def update(self, instance, validated_data):
        file_upload_data = validated_data.pop('file_upload', None)
        file_instance = validated_data.get('file', instance.file)

        with transaction.atomic():
            # if file_upload_data:
            #     file_instance = FileUpload.objects.create(file=file_upload_data)
            # validated_data['file'] = file_instance
            for attr, value in validated_data.items():
                if attr in ['url', 'title', 'priority', 'note']:
                    setattr(instance, attr, value)
            instance.save()
            return instance


class BannerItemWrite(serializers.ModelSerializer):
    file_upload = serializers.FileField(allow_null=True, write_only=True)

    class Meta:
        model = BannerItem
        exclude = ['id', 'banner', 'created_at']
        extra_kwargs = {
            'note': {'write_only': True},
            'file': {'write_only': True},
            'video_url': {'required': False}
        }

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        try:
            representation['file_url'] = APP_SERVER + instance.file.file.url if instance.file else None
        except AttributeError:
            pass
        return representation


class BannerSerializer(serializers.ModelSerializer):
    banner_items = BannerItemWrite(many=True, required=False)

    class Meta:
        model = Banner
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')
        extra_kwargs = {
            'display_type': {'required': True}
        }

    def create(self, validated_data):
        banner_items_data = validated_data.pop('banner_items', [])
        with transaction.atomic():
            banner = Banner.objects.create(**validated_data)
            self.create_or_update_banner_items(banner, banner_items_data)
            return banner

    def update(self, instance, validated_data):
        banner_items_data = validated_data.pop('banner_items', [])
        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            instance.banner_items.all().delete()
            self.create_or_update_banner_items(instance, banner_items_data)
            return instance

    def create_or_update_banner_items(self, banner, banner_items_data):
        existing_items = {item.id: item for item in banner.banner_items.all()}
        for banner_item_data in banner_items_data:
            item_id = banner_item_data.get('id')
            if item_id and item_id in existing_items:
                banner_item = existing_items[item_id]
                for attr in ['url', 'title', 'priority', 'note']:
                    if attr in banner_item_data:
                        setattr(banner_item, attr, banner_item_data[attr])
                banner_item.save()
            else:
                self.create_or_update_banner_items(banner, [banner_item_data])
