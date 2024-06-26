from django.db import transaction
from rest_framework import serializers

from app import settings
from app.logs import app_log
from marketing.medias.models import Banner, BannerItem
from system.file_upload.api.serializers import FileShortViewSerializer
from system.file_upload.models import FileUpload
from utils.env import APP_SERVER


class BannerItemSerializer(serializers.ModelSerializer):
    file_upload = serializers.FileField(allow_null=True, write_only=True)

    class Meta:
        model = BannerItem
        fields = '__all__'
        read_only_fields = ('id', 'created_at')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if request:
            app_log.info(f"In request")
            representation['file_url'] = request.build_absolute_uri(instance.file.file.url)
        else:
            representation['file_url'] = APP_SERVER + instance.file.file.url if instance.file else None
        return representation

    def create(self, validated_data):
        file_upload_data = validated_data.pop('file_upload', None)
        file_instance = validated_data.get('file', None)

        if not file_instance and not file_upload_data:
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
            if file_upload_data:
                file_instance = FileUpload.objects.create(file=file_upload_data)
            validated_data['file'] = file_instance

            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            return instance


class BannerItemWrite(serializers.ModelSerializer):
    file_upload = serializers.FileField(allow_null=True)

    class Meta:
        model = BannerItem
        exclude = ['id', 'banner', 'created_at']

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
    banner_items = BannerItemWrite(many=True)

    class Meta:
        model = Banner
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')

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
        for banner_item_data in banner_items_data:
            file_upload = banner_item_data.pop('file_upload', None)
            file = banner_item_data.pop('file', None)
            if file_upload and file is None:
                file = FileUpload.objects.create(file=file_upload)
            banner_item_data['file'] = file
            banner_item_data['banner'] = banner
            BannerItem.objects.create(**banner_item_data)
