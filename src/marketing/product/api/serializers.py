from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from account.handlers.restrict_serializer import BaseRestrictSerializer
from marketing.product.models import ProductCategory, RegistrationUnit, Producer, RegistrationCert, ProductType, \
    Product, CategoryDetail, UseObject, UseFor
from utils.helpers import normalize_vietnamese as norm_vn


class ProductTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductType
        fields = '__all__'


class RegistrationUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistrationUnit
        fields = '__all__'


class ProducerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producer
        fields = '__all__'


class RegistrationCertSerializer(serializers.ModelSerializer):
    registered_unit = RegistrationUnitSerializer(allow_null=True)
    producer = ProducerSerializer(allow_null=True)

    class Meta:
        model = RegistrationCert
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(RegistrationCertSerializer, self).__init__(*args, **kwargs)
        self.fields['id'].required = False

    def create(self, validated_data):
        id = validated_data.get('id', None)
        if id is None:
            raise serializers.ValidationError({'id': 'This field is required'})
        unit_data = validated_data.pop('registered_unit', None)
        producer_data = validated_data.pop('producer', None)
        # Add unit data if not None
        if unit_data is not None:
            unit, _ = RegistrationUnit.objects.get_or_create(**unit_data)
            validated_data['registered_unit'] = unit
        # Add producer data if not None
        if producer_data is not None:
            producer, _ = Producer.objects.get_or_create(**producer_data)
            validated_data['producer'] = producer
        # Process adding Registration Certificate
        registration_cert = RegistrationCert.objects.create(**validated_data)
        return registration_cert

    def update(self, instance, validated_data):
        unit_data = validated_data.pop('registered_unit', None)
        producer_data = validated_data.pop('producer', None)

        if unit_data:
            unit_serializer = RegistrationUnitSerializer(instance=instance.registered_unit, data=unit_data)
            if unit_serializer.is_valid():
                unit_serializer.save()

        if producer_data:
            producer_serializer = ProducerSerializer(instance=instance.producer, data=producer_data)
            if producer_serializer.is_valid():
                producer_serializer.save()
        return super().update(instance, validated_data)


class ProductCateSerializer(BaseRestrictSerializer):
    registration = RegistrationCertSerializer()
    # files_upload = serializers.ListField(
    #     child=serializers.FileField(max_length=100000, allow_empty_file=False, use_url=False),
    #     write_only=True, required=False)
    content = serializers.ReadOnlyField(source='get_content')

    class Meta:
        model = ProductCategory
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def __init__(self, *args, **kwargs):
        super(ProductCateSerializer, self).__init__(*args, **kwargs)
        if self.instance:
            self.fields['id'].required = False

    def get_content(self):
        return ContentType.objects.get_for_model(self.Meta.model)

    def create(self, validated_data):
        _id = validated_data.get('id', None)
        # files_upload = validated_data.pop('files_upload', [])
        # print(files_upload)
        # for file in files_upload:
        #     print(file)
        if _id is None:
            raise serializers.ValidationError({'id': 'This field is required'})
        # Get data for RegistrationCert
        registration_data = validated_data.pop('registration')
        # Get insert data for Product Category
        insert_data, perm_data = self.split_data(validated_data)
        # Process create RegistrationCert
        registration_cert = RegistrationCertSerializer().create(registration_data)
        # Process create ProductCategory
        product_category = ProductCategory.objects.create(registration=registration_cert, **insert_data)
        print(registration_cert)
        # Create permissions if get restrict
        restrict = perm_data.get('restrict')
        if restrict:
            self.handle_restrict(perm_data, product_category.id, self.Meta.model)
        return product_category

    def update(self, instance, validated_data):
        registration_data = validated_data.pop('registration', None)
        if registration_data:
            reg_serializer = RegistrationCertSerializer(instance=instance.registration, data=registration_data,
                                                        partial=True)
            if reg_serializer.is_valid():
                reg_serializer.save()
        # Get insert data for Product Category
        insert_data, perm_data = self.split_data(validated_data)
        for attr, value in insert_data.items():
            setattr(instance, attr, value)
        restrict = perm_data.get('restrict')
        if restrict:
            self.handle_restrict(perm_data, instance.id, self.Meta.model)
        instance.save()
        return instance


class UseObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = UseObject
        fields = '__all__'
        read_only_fields = ['id']


class UseForSerializer(serializers.ModelSerializer):
    class Meta:
        model = UseFor
        fields = '__all__'
        read_only_fields = ['id']


class CategoryDetailSerializer(serializers.ModelSerializer):
    use_object = UseObjectSerializer()
    use_for = UseForSerializer()

    class Meta:
        model = CategoryDetail
        fields = '__all__'
        read_only_fields = ['id']

    def create(self, validated_data):
        # Get data for UseObject
        use_object_data = validated_data.pop('use_object')
        # Get data for UseFor
        use_for_data = validated_data.pop('use_for')
        # Create CategoryDetail
        cate_detail = CategoryDetail.objects.create(**validated_data)
        using_for, _ = UseFor.objects.get_or_create(id=norm_vn(use_for_data.get('name')), defaults=use_for_data)
        using_object, _ = UseObject.objects.get_or_create(id=norm_vn(use_object_data.get('name')), defaults=use_for_data)
        cate_detail.use_for = using_for
        cate_detail.use_object = using_object
        cate_detail.save()
        return cate_detail

    def update(self, instance, validated_data):
        # Get data for UseObject
        use_object_data = validated_data.pop('use_object')
        # Get data for UseFor
        use_for_data = validated_data.pop('use_for')
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        using_for, _ = UseFor.objects.get_or_create(id=norm_vn(use_for_data.get('name')), defaults=use_for_data)
        using_object, _ = UseObject.objects.get_or_create(id=norm_vn(use_object_data.get('name')), defaults=use_for_data)
        instance.use_for = using_for
        instance.use_object = using_object
        instance.save()
        return instance


class ProductSerializer(BaseRestrictSerializer):
    class Meta:
        model = Product
        fields = '__all__'
