from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from system.file_upload.models import FileUpload, ContentFile, ProductCateFile, ProductFile


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


class FileViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileUpload
        fields = ['id', 'file', 'file_name', 'file_ext', 'type']


class FileShortViewSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = FileUpload
        fields = ['id', 'type', 'file_url']

    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request is not None:
                print("Has request")
                return request.build_absolute_uri(obj.file.url)
            print("Return no request")
            return obj.file.url
        return None


class FileProductCateSerializer(serializers.ModelSerializer):
    file_data = FileViewSerializer(source='file', read_only=True)

    class Meta:
        model = ProductCateFile
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')

    def create(self, validated_data):
        file_data = validated_data.pop('file')
        file_instance = FileUpload.objects.create(**file_data)
        product_file_instance = ProductCateFile.objects.create(file=file_instance, **validated_data)
        return product_file_instance

    def update(self, instance, validated_data):
        file_data = validated_data.pop('file', None)

        if file_data is not None:
            file_serializer = FileUploadSerializer(instance.file, data=file_data, partial=True)
            if file_serializer.is_valid():
                file_serializer.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance


class FileProductCateViewSerializer(serializers.ModelSerializer):
    document = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = ProductCateFile
        fields = ['id', 'priority', 'document', 'image']

    def get_document(self, obj):
        if obj.file and obj.file.type == 'document':
            return FileShortViewSerializer(obj.file, context=self.context).data
        return None

    def get_image(self, obj):
        if obj.file and obj.file.type == 'image':
            return FileShortViewSerializer(obj.file, context=self.context).data
        return None


class FileProductSerializer(serializers.ModelSerializer):
    file = FileUploadSerializer(write_only=True)
    file_data = FileViewSerializer(source='file', read_only=True)

    class Meta:
        model = ProductFile
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')

    def create(self, validated_data):
        file_data = validated_data.pop('file')
        file_instance = FileUpload.objects.create(**file_data)
        product_file_instance = ProductFile.objects.create(file=file_instance, **validated_data)
        return product_file_instance

    def update(self, instance, validated_data):
        file_data = validated_data.pop('file', None)

        if file_data is not None:
            file_serializer = FileUploadSerializer(instance.file, data=file_data, partial=True)
            if file_serializer.is_valid():
                file_serializer.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance
