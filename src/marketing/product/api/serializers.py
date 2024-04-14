from account.handlers.restrict_serializer import BaseRestrictSerializer
from marketing.product.models import ProductCategory, RegistrationUnit, Producer, RegistrationCert, ProductType, Product


class ProductTypeSerializer(BaseRestrictSerializer):
    class Meta:
        model = ProductType
        fields = '__all__'


class RegistrationUnitSerializer(BaseRestrictSerializer):
    class Meta:
        model = RegistrationUnit
        fields = '__all__'


class ProducerSerializer(BaseRestrictSerializer):
    class Meta:
        model = Producer
        fields = '__all__'


class RegistrationCertSerializer(BaseRestrictSerializer):
    class Meta:
        model = RegistrationCert
        fields = '__all__'


class ProductCateSerializer(BaseRestrictSerializer):
    class Meta:
        model = ProductCategory
        fields = '__all__'


class ProductSerializer(BaseRestrictSerializer):
    class Meta:
        model = Product
        fields = '__all__'
