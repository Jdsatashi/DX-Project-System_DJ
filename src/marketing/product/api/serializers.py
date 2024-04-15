from rest_framework import serializers

from account.handlers.restrict_serializer import BaseRestrictSerializer
from marketing.product.models import ProductCategory, RegistrationUnit, Producer, RegistrationCert, ProductType, Product


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

    def create(self, validated_data):
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

    class Meta:
        model = ProductCategory
        fields = '__all__'

    def create(self, validated_data):
        # Get data for RegistrationCert
        registration_data = validated_data.pop('registration')
        # Get insert data for Product Category
        insert_data, perm_data = self.split_data(validated_data)
        # Process create RegistrationCert
        registration_cert = RegistrationCertSerializer().create(registration_data)
        # Process create ProductCategory
        product_category = ProductCategory.objects.create(registration=registration_cert, **insert_data)
        # Create permissions if get restrict
        restrict = perm_data.get('restrict')
        if restrict:
            self.handle_restrict(perm_data, product_category.id, self.Meta.model)
        return product_category

    def update(self, instance, validated_data):
        registration_data = validated_data.pop('registration', None)
        if registration_data:
            reg_serializer = RegistrationCertSerializer(instance=instance.registration, data=registration_data)
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



class ProductSerializer(BaseRestrictSerializer):
    class Meta:
        model = Product
        fields = '__all__'

    def create(self, validated_data):
        data, perm_data = self.split_data(validated_data)
        # Restrict check if create request required perm
        restrict = perm_data.get('restrict')
        instance = super().create(data)
        # When required quyen, handle to add perm
        if restrict:
            self.handle_restrict(perm_data, instance.id, self.Meta.model)
        return instance
