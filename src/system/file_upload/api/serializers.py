from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from system.file_upload.models import FileUpload, ContentFile, ProductCateFile, ProductFile
from utils.env import APP_SERVER


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
        read_only_fields = ('id', 'file_name', 'file_ext', 'type')
        extra_kwargs = {
            'file': {'write_only': True}
        }

    def to_representation(self, instance: FileUpload):
        ret = super().to_representation(instance)
        file_url = APP_SERVER + instance.file.url if instance.file.url else None
        ret['file'] = file_url
        return ret


class FileShortViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileUpload
        fields = ['id', 'type', 'file']


class FileCateShortView(serializers.ModelSerializer):
    file_data = FileShortViewSerializer(source='file', read_only=True)

    class Meta:
        model = ProductCateFile
        fields = ['priority', 'docs_type', 'file_data']


class FileProductCateSerializer(serializers.ModelSerializer):
    file_data = FileViewSerializer(write_only=True, required=False)

    class Meta:
        model = ProductCateFile
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['file_data'] = FileViewSerializer(instance.file).data
        return ret

    def create(self, validated_data):
        file_instance = validated_data.pop('file', None)
        file_data = validated_data.pop('file_data', None)

        if not file_instance:
            if not file_data:
                raise serializers.ValidationError({'message': 'yêu cầu file: id hoặc file_data.file: file mới'})
            file_instance = FileUpload.objects.create(file=file_data.get('file'))
            print(f"Create new file: {file_instance}")
        product_file_instance = ProductCateFile.objects.create(file=file_instance, **validated_data)
        return product_file_instance

    def update(self, instance, validated_data):
        file_instance = validated_data.pop('file', None)
        file_data = validated_data.pop('file_data', None)

        if not file_instance:
            if not file_data:
                raise serializers.ValidationError({'message': 'yêu cầu file: id hoặc file_data.file: file mới'})
            file_instance = FileUpload.objects.create(file=file_data.get('file'))

        validated_data['file'] = file_instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance


class FileProductCateViewSerializer(serializers.ModelSerializer):
    document = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = ProductCateFile
        fields = ['id', 'priority', 'docs_type', 'document', 'image']

    def get_document(self, obj):
        if obj.file and obj.file.type == 'document':
            return FileShortViewSerializer(obj.file, context=self.context).data
        return None

    def get_image(self, obj):
        if obj.file and obj.file.type == 'image':
            return FileShortViewSerializer(obj.file, context=self.context).data
        return None


class FileProductViewSerializer(serializers.ModelSerializer):
    document = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = ProductFile
        fields = ['id', 'priority', 'docs_type', 'document', 'image']

    def get_document(self, obj):
        if obj.file and obj.file.type == 'document':
            return FileShortViewSerializer(obj.file, context=self.context).data
        return None

    def get_image(self, obj):
        if obj.file and obj.file.type == 'image':
            return FileShortViewSerializer(obj.file, context=self.context).data
        return None


class FileProductSerializer(serializers.ModelSerializer):
    # file = FileUploadSerializer(write_only=True, required=False)
    file = serializers.FileField(write_only=True, required=False)
    file_note = serializers.CharField(write_only=True, required=False)
    file_data = FileViewSerializer(source='file', read_only=True)

    class Meta:
        model = ProductFile
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')

    def create(self, validated_data):
        file_data = validated_data.pop('file', None)
        file_note = validated_data.pop('file_note', None)
        # if file_data is None:
        #     raise serializers.ValidationError({"message": 'dữ liệu file là bắt buộc'})
        file_instance = FileUpload.objects.create(file=file_data, note=file_note)
        product_file_instance = ProductFile.objects.create(file=file_instance, **validated_data)
        return product_file_instance

    def update(self, instance, validated_data):
        file_data = validated_data.pop('file', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance
