from functools import partial

from rest_framework import viewsets, mixins, status
from rest_framework.authentication import BasicAuthentication
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from account.handlers.validate_perm import ValidatePermRest
from marketing.product.api.serializers import ProductTypeSerializer, ProductCateSerializer, RegistrationCertSerializer, \
    ProducerSerializer, RegistrationUnitSerializer, ProductSerializer, CategoryDetailSerializer, ProductIdSerializer, \
    UseObjectSerializer, UseForSerializer
from marketing.product.models import ProductType, ProductCategory, RegistrationCert, Producer, RegistrationUnit, \
    Product, CategoryDetail, UseObject, UseFor
from utils.model_filter_paginate import filter_data


class GenericApiProductType(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                            mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = ProductTypeSerializer
    queryset = ProductType.objects.all()

    # authentication_classes = [JWTAuthentication, BasicAuthentication]
    # permission_classes = [partial(ValidatePermRest, model=ProductType)]
    def list(self, request, *args, **kwargs):
        response_data = filter_data(self, request, ['id', 'name'], **kwargs)
        return Response(response_data, status=status.HTTP_200_OK)


class GenericApiRegistrationUnit(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                                 mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = RegistrationUnitSerializer
    queryset = RegistrationUnit.objects.all()

    # authentication_classes = [JWTAuthentication, BasicAuthentication]
    # permission_classes = [partial(ValidatePermRest, model=RegistrationUnit)]
    def list(self, request, *args, **kwargs):
        response_data = filter_data(self, request, ['id', 'unit', 'address'], **kwargs)
        return Response(response_data, status=status.HTTP_200_OK)


class GenericApiProducer(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                         mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = ProducerSerializer
    queryset = Producer.objects.all()

    # authentication_classes = [JWTAuthentication, BasicAuthentication]
    # permission_classes = [partial(ValidatePermRest, model=Producer)]
    def list(self, request, *args, **kwargs):
        response_data = filter_data(self, request, ['id', 'name', 'address'], **kwargs)
        return Response(response_data, status=status.HTTP_200_OK)


class GenericApiRegistrationCert(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                                 mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = RegistrationCertSerializer
    queryset = RegistrationCert.objects.all()

    # authentication_classes = [JWTAuthentication, BasicAuthentication]
    # permission_classes = [partial(ValidatePermRest, model=RegistrationCert)]

    def list(self, request, *args, **kwargs):
        response_data = filter_data(self, request, ['id', 'registered_unit__id', 'producer__id'], **kwargs)
        return Response(response_data, status=status.HTTP_200_OK)


class GenericApiProductCategory(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                                mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = ProductCateSerializer
    queryset = ProductCategory.objects.all()

    # authentication_classes = [JWTAuthentication, BasicAuthentication]
    # permission_classes = [partial(ValidatePermRest, model=ProductCategory)]

    def list(self, request, *args, **kwargs):
        response_data = filter_data(self, request, ['id', 'name', 'product_type__name', 'product_type__id'], **kwargs)
        return Response(response_data, status=status.HTTP_200_OK)


class GenericApiCategoryDetail(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                               mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = CategoryDetailSerializer
    queryset = CategoryDetail.objects.all()

    # authentication_classes = [JWTAuthentication, BasicAuthentication]
    # permission_classes = [partial(ValidatePermRest, model=ProductCategory)]

    def list(self, request, *args, **kwargs):
        response_data = filter_data(self, request, ['cate_id__id', 'use_object__name', 'use_for__name'], **kwargs)
        return Response(response_data, status=status.HTTP_200_OK)


class GenericApiProduct(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                        mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = ProductSerializer
    queryset = Product.objects.all()

    # authentication_classes = [JWTAuthentication, BasicAuthentication]
    # permission_classes = [partial(ValidatePermRest, model=Product)]

    def list(self, request, *args, **kwargs):
        response_data = filter_data(self, request, ['id', 'name', 'category__id', 'category__name'], **kwargs)
        return Response(response_data, status=status.HTTP_200_OK)


class ApiProductId(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = ProductIdSerializer
    queryset = Product.objects.all()


class ApiUseObject(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = UseObjectSerializer
    queryset = UseObject.objects.all()

    # authentication_classes = [JWTAuthentication, BasicAuthentication]
    # permission_classes = [partial(ValidatePermRest, model=Product)]

    def list(self, request, *args, **kwargs):
        response_data = filter_data(self, request, ['id', 'name'], **kwargs)
        return Response(response_data, status=status.HTTP_200_OK)


class ApiUseFor(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = UseForSerializer
    queryset = UseFor.objects.all()

    # authentication_classes = [JWTAuthentication, BasicAuthentication]
    # permission_classes = [partial(ValidatePermRest, model=Product)]

    def list(self, request, *args, **kwargs):
        response_data = filter_data(self, request, ['id', 'name'], **kwargs)
        return Response(response_data, status=status.HTTP_200_OK)
