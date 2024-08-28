from rest_framework import serializers

from account.handlers.restrict_serializer import BaseRestrictSerializer
from app.logs import app_log
from marketing.company.models import Company
from marketing.product.models import ProductCategory, RegistrationUnit, Producer, RegistrationCert, ProductType, \
    Product, CategoryDetail, UseObject, UseFor
from system.file_upload.api.serializers import FileProductCateViewSerializer

from utils.helpers import normalize_vietnamese as norm_vn


class ProductTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductType
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class ViewProductTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductType
        fields = ['id', 'name']


class RegistrationUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistrationUnit
        fields = '__all__'


class ProducerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producer
        fields = '__all__'


class ProductCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'name']


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
        print(f"unit data: {unit_data}")
        print(f"producer_data data: {producer_data}")
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
    registration = RegistrationCertSerializer(read_only=True)
    product_type = ViewProductTypeSerializer(read_only=True)
    company = ProductCompanySerializer(read_only=True)

    registration_id = serializers.CharField(required=True)
    product_type_id = serializers.CharField(required=True)
    company_id = serializers.CharField(required=True)

    class Meta:
        model = ProductCategory
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def __init__(self, *args, **kwargs):
        super(ProductCateSerializer, self).__init__(*args, **kwargs)
        if self.instance:
            self.fields['id'].required = False

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        files = instance.product_cate_files.all()
        files_fields_details(request, files, representation)
        return representation

    def create(self, validated_data):
        _id = validated_data.get('id', None)
        if _id is None:
            raise serializers.ValidationError({'id': 'This field is required'})
        # Get insert data for Product Category
        insert_data, perm_data = self.split_data(validated_data)
        # Process create RegistrationCert
        registration_id = insert_data.get('registration_id')
        product_type_id = insert_data.get('product_type_id')
        company_id = insert_data.get('company_id')
        registration_cert = RegistrationCert.objects.filter(id=registration_id).first()
        if registration_cert is None:
            raise serializers.ValidationError({'message': f'not found registration certificate {registration_id}'})
        company = Company.objects.filter(id=company_id).first()
        if company is None:
            raise serializers.ValidationError({'message': f'not found company {company_id}'})
        product_type = ProductType.objects.filter(id=product_type_id).first()
        if product_type is None:
            raise serializers.ValidationError({'message': f'not found product type {product_type_id}'})
        insert_data['product_type'] = product_type
        insert_data['company'] = company
        # Process create ProductCategory
        product_category = ProductCategory.objects.create(registration=registration_cert, **insert_data)
        app_log.info(registration_cert)
        # Create permissions if get restrict
        restrict = perm_data.get('restrict')
        if restrict:
            self.handle_restrict(perm_data, product_category.id, self.Meta.model)
        return product_category

    def update(self, instance, validated_data):
        _id = validated_data.pop('id', None)

        # Get insert data for Product Category
        insert_data, perm_data = self.split_data(validated_data)

        # Process update RegistrationCert
        registration_id = insert_data.get('registration_id')
        product_type_id = insert_data.get('product_type_id')
        company_id = insert_data.get('company_id')

        if registration_id:
            registration_cert = RegistrationCert.objects.filter(id=registration_id).first()
            if registration_cert is None:
                raise serializers.ValidationError({'message': f'not found registration certificate {registration_id}'})
            instance.registration = registration_cert

        if product_type_id:
            product_type = ProductType.objects.filter(id=product_type_id).first()
            if product_type is None:
                raise serializers.ValidationError({'message': f'not found product type {product_type_id}'})
            instance.product_type = product_type

        if company_id:
            company = Company.objects.filter(id=company_id).first()
            if company is None:
                raise serializers.ValidationError({'message': f'not found company {company_id}'})
            instance.company = company

        # Update the other fields
        for attr, value in insert_data.items():
            setattr(instance, attr, value)

        # Handle restrict permissions
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


# Product Category Detail serializers for Api CRUD Views
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
        using_object, _ = UseObject.objects.get_or_create(id=norm_vn(use_object_data.get('name')),
                                                          defaults=use_for_data)
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
        using_object, _ = UseObject.objects.get_or_create(id=norm_vn(use_object_data.get('name')),
                                                          defaults=use_for_data)
        instance.use_for = using_for
        instance.use_object = using_object
        instance.save()
        return instance


# Product serializers for Api CRUD Views
class ProductSerializer(BaseRestrictSerializer):
    category_details = ProductCateSerializer(source='category', read_only=True)

    product_type = ViewProductTypeSerializer(read_only=True)

    class Meta:
        model = Product
        fields = '__all__'


class ProductIdSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'category']


# Support functions
def files_fields_details(request, files, representation):
    # Get file add to serializer
    file_serializer = FileProductCateViewSerializer(files, many=True, context={'request': request})
    # Split files to document and image
    documents = []
    images = []
    for file_data in file_serializer.data:
        if file_data['document'] is not None:
            file_data['document'].update({'priority': file_data['priority'], 'docs_type': file_data['docs_type']})

            documents.append(file_data['document'])
        if file_data['image'] is not None:
            file_data['image'].update({'priority': file_data['priority'], 'docs_type': file_data['docs_type']})
            images.append(file_data['image'])
    representation['files'] = {
        'documents': documents,
        'images': images
    }
