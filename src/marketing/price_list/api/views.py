import os
from functools import partial

import pandas
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, mixins, status
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from account.handlers.perms import perm_queryset
from account.handlers.validate_perm import ValidatePermRest
from app.logs import app_log
from marketing.price_list.api.serializers import PriceListSerializer, SpecialOfferSerializer, PriceList2Serializer
from marketing.price_list.models import PriceList, SpecialOffer, ProductPrice
from marketing.product.models import Product
from utils.model_filter_paginate import filter_data


class GenericApiPriceList(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                          mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = PriceListSerializer
    # queryset = PriceList.objects.all()
    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]

    permission_classes = [partial(ValidatePermRest, model=PriceList)]

    def get_queryset(self):
        app_log.info(f"Getting query set")
        return perm_queryset(self)

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['id', 'name', 'date_start', 'date_end'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)

    @action(methods=['get'], detail=False, url_path='now', url_name='now')
    def now(self, request, *args, **kwargs):
        today = timezone.localdate()
        queryset = self.get_queryset().filter(date_start__lte=today, date_end__gte=today)
        response = filter_data(self, request, ['id', 'name', 'date_start', 'date_end'], queryset=queryset,
                               **kwargs)
        return Response(response)


class ApiSpecialOffer(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                      mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = SpecialOfferSerializer
    # queryset = SpecialOffer.objects.all()
    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]
    permission_classes = [partial(ValidatePermRest, model=PriceList)]

    def get_queryset(self):
        return perm_queryset(self)

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['id', 'name', 'status', 'type_list'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)


class ApiSpecialOfferConsider(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = SpecialOfferSerializer
    queryset = SpecialOffer.objects.filter(type_list='consider_offer_user')
    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]

    # permission_classes = [partial(ValidatePermRest, model=PriceList)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['id', 'name', 'status'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)


class ApiImportProductPL(APIView):
    def post(self, request, *args, **kwargs):
        app_log.info(f"Importing product price list")
        excel_file = self.request.FILES.get('excel_file', None)
        app_log.info(f"Test excel file: {str(excel_file)}")
        # Validate
        if excel_file is None:
            return Response({"message": "not found excel import file"}, status=status.HTTP_400_BAD_REQUEST)
        # Validate file extension
        file_extension = os.path.splitext(excel_file.name)[1].lower()
        if file_extension not in ['.xls', '.xlsx']:
            return Response({"message": "Invalid file format. Only .xls and .xlsx files are supported."},
                            status=status.HTTP_400_BAD_REQUEST)

        price_list_id = self.request.data.get('price_list', None)
        if price_list_id is None:
            return Response({"message": "field price_list is required"}, status=status.HTTP_400_BAD_REQUEST)
        price_list = PriceList.objects.filter(id=price_list_id)
        if not price_list.exists():
            return Response({"message": f"price list with id {price_list_id} not found"},
                            status=status.HTTP_400_BAD_REQUEST)
        price_list = price_list.first()
        try:
            with transaction.atomic():
                excel_data = pandas.read_excel(excel_file, usecols="A:D")

                bulk_create_list = []
                bulk_update_list = []
                product_ids_in_excel = []

                for index, row in excel_data.iterrows():
                    product_id = row['maSanPham']
                    product_price = row['donGia']
                    quantity_in_box = row['soLuongTrenThung']
                    point = row['diemTrenThung']

                    try:
                        product = Product.objects.get(id=product_id)
                    except Product.DoesNotExist:
                        return Response({"message": f"Product with id {product_id} not found"},
                                        status=status.HTTP_400_BAD_REQUEST)

                    product_ids_in_excel.append(product_id)

                    product_price_object = ProductPrice.objects.filter(price_list=price_list, product=product).first()
                    if product_price_object:
                        product_price_object.price = product_price
                        product_price_object.quantity_in_box = quantity_in_box
                        product_price_object.point = point
                        bulk_update_list.append(product_price_object)
                    else:
                        product_price_object = ProductPrice(
                            price_list=price_list,
                            product=product,
                            price=product_price,
                            quantity_in_box=quantity_in_box,
                            point=point
                        )
                        bulk_create_list.append(product_price_object)

                # Bulk create new entries
                if bulk_create_list:
                    ProductPrice.objects.bulk_create(bulk_create_list)
                # Bulk update existing entries
                if bulk_update_list:
                    ProductPrice.objects.bulk_update(bulk_update_list, ['price', 'quantity_in_box', 'point'])

                # Remove products not in the current Excel file
                ProductPrice.objects.filter(price_list=price_list).exclude(
                    product__id__in=product_ids_in_excel).delete()

            data = PriceList2Serializer(price_list).data
            return Response({"message": "Price list updated successfully", "data": data}, status=status.HTTP_200_OK)
        except Exception as e:
            app_log.info(f"Error when updating product price")
            raise e
