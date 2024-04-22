from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from system.file_upload.models import FileUpload, ContentFile


class ContentTypeField(serializers.Field):
    def to_representation(self, value):
        return value.model

    def to_internal_value(self, data):
        try:
            return ContentType.objects.get(model=data)
        except ContentType.DoesNotExist:
            raise serializers.ValidationError("ContentType không hợp lệ.")


class ContentFileSerialier(serializers.ModelSerializer):
    content_object = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ContentFile
        fields = '__all__'
        read_only_fields = ('content_object', 'created_at', 'updated_at')
        write_only_fields = ['file']

    @staticmethod
    def get_content_object(self, obj):
        return str(obj.content_object)


class FileUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileUpload
        fields = '__all__'
        read_only_fields = ('id', 'file_name', 'file_ext', 'type', 'created_at', 'updated_at')
