from functools import partial

from rest_framework import viewsets, mixins
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication

from account.handlers.validate_perm import ValidatePermRest
from marketing.product.api.serializers import ProductTypeSerializer, ProductCateSerializer, RegistrationCertSerializer, \
    ProducerSerializer, RegistrationUnitSerializer, ProductSerializer
from marketing.product.models import ProductType, ProductCategory, RegistrationCert, Producer, RegistrationUnit, Product


class GenericApiProductType(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                            mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = ProductTypeSerializer
    queryset = ProductType.objects.all()
    # authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]
    # permission_classes = [partial(ValidatePermRest, model=ProductType)]


class GenericApiRegistrationUnit(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                                 mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = RegistrationUnitSerializer
    queryset = RegistrationUnit.objects.all()
    # authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]
    # permission_classes = [partial(ValidatePermRest, model=RegistrationUnit)]


class GenericApiProducer(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                         mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = ProducerSerializer
    queryset = Producer.objects.all()
    # authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]
    # permission_classes = [partial(ValidatePermRest, model=Producer)]


class GenericApiRegistrationCert(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                                 mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = RegistrationCertSerializer
    queryset = RegistrationCert.objects.all()
    # authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]
    # permission_classes = [partial(ValidatePermRest, model=RegistrationCert)]


class GenericApiProductCategory(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                                mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = ProductCateSerializer
    queryset = ProductCategory.objects.all()
    # authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]
    # permission_classes = [partial(ValidatePermRest, model=ProductCategory)]


class GenericApiProduct(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                                mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = ProductSerializer
    queryset = Product.objects.all()
    # authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]
    # permission_classes = [partial(ValidatePermRest, model=Product)]
