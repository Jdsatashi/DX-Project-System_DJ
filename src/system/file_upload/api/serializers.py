from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from system.file_upload.models import FileUpload


class ContentTypeField(serializers.Field):
    def to_representation(self, value):
        # Chuyển đổi đối tượng ContentType thành tên model khi serializing
        return value.model

    def to_internal_value(self, data):
        # Chuyển đổi tên model nhập vào thành đối tượng ContentType khi deserializing
        try:
            return ContentType.objects.get(model=data)
        except ContentType.DoesNotExist:
            raise serializers.ValidationError("ContentType không hợp lệ.")


class FileUploadSerializer(serializers.ModelSerializer):
    content_type = ContentTypeField()
    class Meta:
        model = FileUpload
        fields = '__all__'
        read_only_fields = ('file_name', 'file_ext', 'id', 'created_at', 'created_at')
