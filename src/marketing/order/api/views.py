import json
import time
from datetime import datetime, timedelta
from functools import partial
from io import BytesIO

import openpyxl
import pandas as pd
from django.core.exceptions import FieldError
from django.core.paginator import Paginator
from django.db.models import Prefetch, QuerySet
from django.db.models import Sum, Q, Case, When, FloatField, F
from django.db.models.functions import Abs, Coalesce
from django.http import HttpResponse
from django.http import StreamingHttpResponse
from django.utils import timezone
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
from rest_framework import viewsets, mixins, status
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import AccessToken

from account.handlers.perms import DataFKModel, get_perm_name
from account.handlers.validate_perm import ValidatePermRest
from account.models import User
from app.logs import app_log
from marketing.order.api.serializers import OrderSerializer, ProductStatisticsSerializer, SeasonalStatisticSerializer, \
    SeasonStatsUserPointSerializer
from marketing.order.models import Order, OrderDetail, SeasonalStatistic, SeasonalStatisticUser
from marketing.price_list.models import SpecialOffer
from user_system.client_profile.models import ClientProfile
from user_system.employee_profile.models import EmployeeProfile
from utils.constants import maNhomND, so_type
from utils.model_filter_paginate import filter_data, get_query_parameters, build_absolute_uri_with_params


class GenericApiOrder(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                      mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = OrderSerializer
    queryset = Order.objects.all()
    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]

    permission_classes = [partial(ValidatePermRest, model=Order)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['id', 'date_get', 'date_company_get', 'client_id__id'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        serializer.delete(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def users_order(self, request, *args, **kwargs):
        user_id = request.query_params.get('user', '')
        if user_id == '':
            user = request.user
        else:
            current_user = request.user
            user = User.objects.filter(id=user_id.upper()).first()
        app_log.info(f"User test: {user}")
        orders = Order.objects.filter(client_id=user)
        response = filter_data(self, request, ['id', 'date_get', 'date_company_get', 'client_id'], queryset=orders,
                               **kwargs)
        return Response(response, status.HTTP_200_OK)


class ProductStatisticsView(APIView):
    permission_classes = [partial(ValidatePermRest, model=Order)]
    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]
    serializer_class = ProductStatisticsSerializer

    def get(self, request, *args, **kwargs):
        try:
            # Get current user
            user_id = request.query_params.get('user', '')
            user = request.user
            if user_id != '':
                current_user = user
                user = User.objects.filter(id=user_id.upper()).first()
                perm_name = get_perm_name(User)
                if current_user.is_allow(perm_name) or current_user.is_group_has_perm(perm_name):
                    app_log.info(f"User {current_user.id} has permission of {user.id}")
                #     return Response({"error": "User not has permission"}, status=status.HTTP_403_FORBIDDEN)
            app_log.info(f"Test user id: {user}")

            now = datetime.now().date()
            # Set date default
            default_start_date = now - timedelta(days=365)
            default_end_date = now

            # Get params queries
            start_date_1 = request.data.get('start_date_1', datetime.strftime(default_start_date, '%d/%m/%Y'))
            end_date_1 = request.data.get('end_date_1', datetime.strftime(default_end_date, '%d/%m/%Y'))

            start_date_time = datetime.strptime(start_date_1, '%d/%m/%Y')
            start_date_2 = request.data.get('start_date_2',
                                            datetime.strftime(start_date_time - timedelta(days=365), '%d/%m/%Y'))
            end_date_2 = request.data.get('end_date_2',
                                          datetime.strftime(start_date_time - timedelta(days=1), '%d/%m/%Y'))
            # Get type to calculate
            type_statistic = request.data.get('type_statistic') or request.query_params.get('type_statistic', 'all')
            # Add date period compare to dict
            input_date = {'start_date_1': start_date_1, 'end_date_1': end_date_1,
                          'start_date_2': start_date_2, 'end_date_2': end_date_2}
            # Get products as
            product_query = request.query_params.get('products', '')
            # Combine products to list id
            product_ids = product_query.split(',') if product_query else []

            # Get param variables data
            limit = request.query_params.get('limit', 10)
            page = int(request.query_params.get('page', 1))

            # Get queries and paginate order
            details_1, details_2 = self.paginate_orders(user, input_date, product_ids, type_statistic, limit, page)
            # Process calculate cashback
            statistics = self.statistic_calculate(details_1, details_2)
            # Add data to list
            statistics_list = [{"product_id": k, **v} for k, v in statistics.items()]

            if int(limit) == 0:
                serializer = ProductStatisticsSerializer(statistics_list, many=True)
                response_data = {
                    'data': serializer.data,
                    'total_page': 1,
                    'current_page': 1
                }
                return Response(response_data, status=status.HTTP_200_OK)

            # Paginate data
            paginator = Paginator(statistics_list, limit)
            page_obj = paginator.get_page(page)
            serializer = ProductStatisticsSerializer(page_obj, many=True)

            response_data = {
                'data': serializer.data,
                'total_page': paginator.num_pages,
                # 'total_page': self.total_pages,
                'current_page': page
            }
            if page < paginator.num_pages:
                next_page = request.build_absolute_uri(
                    f'?page={page + 1}&limit={limit}&user={user}&type_statistic={type_statistic}&products={product_query}')
                response_data['next_page'] = next_page
            if page > 1:
                prev_page = request.build_absolute_uri(
                    f'?page={page - 1}&limit={limit}&user={user}&type_statistic={type_statistic}&products={product_query}')
                response_data['prev_page'] = prev_page
            return Response(response_data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            raise e
            # return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def paginate_orders(self, user, input_date, product_ids, type_statistic, limit, page):
        start_date_1, end_date_1, start_date_2, end_date_2 = self.convert_dates(input_date)
        app_log.info(f"Paginate test page: {page} | {limit}")
        app_log.info(f"Test datetime: {start_date_1} to {end_date_1} | {start_date_2} | to {end_date_2}")
        orders_1 = Order.objects.filter(client_id=user, date_get__gte=start_date_1, date_get__lte=end_date_1)
        orders_2 = Order.objects.filter(client_id=user, date_get__gte=start_date_2, date_get__lte=end_date_2)

        if len(product_ids) > 0:
            orders_1 = orders_1.filter(order_detail__product_id__in=product_ids).distinct()
            orders_2 = orders_2.filter(order_detail__product_id__in=product_ids).distinct()

        match type_statistic:
            case 'special_offer':
                orders_1 = orders_1.filter(Q(new_special_offer__isnull=False) | Q(is_so=True))
                orders_2 = orders_2.filter(Q(new_special_offer__isnull=False) | Q(is_so=True))
            case 'normal':
                orders_1 = orders_1.filter(
                    Q(new_special_offer__isnull=True) & Q(Q(is_so=False) | Q(is_so__isnull=True)))
                orders_2 = orders_2.filter(
                    Q(new_special_offer__isnull=True) & Q(Q(is_so=False) | Q(is_so__isnull=True)))

        orders_1 = orders_1.order_by('-id')
        orders_2 = orders_2.order_by('-id')

        order_ids_1 = orders_1.values_list('id', flat=True)
        order_ids_2 = orders_2.values_list('id', flat=True)

        query_data_1 = Q(order_id__in=order_ids_1)
        query_data_2 = Q(order_id__in=order_ids_2)

        if len(product_ids) > 0:
            query_data_1 &= Q(product_id__in=product_ids)
            query_data_2 &= Q(product_id__in=product_ids)

        details_1 = OrderDetail.objects.filter(query_data_1).values('product_id', 'product_id__name').annotate(
            total_quantity=Sum('order_quantity'),
            total_point=Sum('point_get'),
            total_price=Sum('product_price'),
            total_box=Sum('order_box'),
            total_cashback=Sum(Case(
                When(price_list_so__isnull=False, then=Abs(Coalesce(F('price_list_so'), 0.0)) * F('order_box')),
                default=0,
                output_field=FloatField()
            ))
        )
        details_2 = OrderDetail.objects.filter(query_data_2).values('product_id', 'product_id__name').annotate(
            total_quantity=Sum('order_quantity'),
            total_point=Sum('point_get'),
            total_price=Sum('product_price'),
            total_box=Sum('order_box'),
            total_cashback=Sum(Case(
                When(price_list_so__isnull=False, then=Abs(Coalesce(F('price_list_so'), 0.0)) * F('order_box')),
                default=0,
                output_field=FloatField()
            ))
        )

        return details_1, details_2

    def convert_dates(self, input_date):
        start_date_1 = timezone.make_aware(datetime.strptime(input_date.get('start_date_1'), '%d/%m/%Y'),
                                           timezone.get_current_timezone())
        end_date_1 = timezone.make_aware(
            datetime.strptime(input_date.get('end_date_1'), '%d/%m/%Y') + timedelta(days=1) - timedelta(seconds=1),
            timezone.get_current_timezone())

        start_date_2 = timezone.make_aware(datetime.strptime(input_date.get('start_date_2'), '%d/%m/%Y'),
                                           timezone.get_current_timezone())
        end_date_2 = timezone.make_aware(
            datetime.strptime(input_date.get('end_date_2'), '%d/%m/%Y') + timedelta(days=1) - timedelta(seconds=1),
            timezone.get_current_timezone())

        return start_date_1, end_date_1, start_date_2, end_date_2

    @staticmethod
    def statistic_calculate(details_1, details_2):
        # Combine results into a single dictionary
        combined_results = {}

        for detail in details_1:
            product_id = detail['product_id']
            product_name = detail['product_id__name']

            combined_results[product_id] = {
                "product_name": product_name,
                "current": {
                    "price": detail['total_price'],
                    "point": detail['total_point'],
                    "quantity": detail['total_quantity'],
                    "box": detail['total_box'],
                    "cashback": int(detail['total_cashback'])
                },
                "total_cashback": int(detail['total_cashback'])
            }

        for detail in details_2:
            product_id = detail['product_id']
            product_name = detail['product_id__name']

            if product_id not in combined_results:
                combined_results[product_id] = {
                    "product_name": product_name,
                    "one_year_ago": {}
                }
            # Calculate total cashback for previous period
            first_cashback = combined_results[product_id].get("total_cashback", 0)
            combined_results[product_id]["one_year_ago"] = {
                "price": detail['total_price'],
                "point": detail['total_point'],
                "quantity": detail['total_quantity'],
                "box": detail['total_box'],
                "cashback": int(detail['total_cashback'])
            }
            combined_results[product_id]["total_cashback"] = first_cashback + int(detail['total_cashback'])

        return combined_results


class ExportReport(APIView):
    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]
    permission_classes = [partial(ValidatePermRest, model=Order)]

    def get(self, request):
        start_time = time.time()
        orders = handle_order(request)

        response = StreamingHttpResponse(
            generate_order_excel(orders),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename=BangToa_{datetime.now().strftime("%d-%m-%Y")}.xlsx'

        print(f"Time export to excel: {time.time() - start_time}")
        return response


class TotalStatisticsView(APIView):
    permission_classes = [partial(ValidatePermRest, model=Order)]
    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]

    def get(self, request, *args, **kwargs):
        try:
            # Get current user
            user_id = request.query_params.get('user', '')
            user = request.user
            if user_id != '':
                current_user = user
                user = User.objects.filter(id=user_id.upper()).first()
                perm_name = get_perm_name(User)
                if current_user.is_allow(perm_name) or current_user.is_group_has_perm(perm_name):
                    app_log.info(f"User {current_user.id} has permission of {user.id}")

            now = datetime.now().date()
            default_start_date = now - timedelta(days=365)
            default_end_date = now

            start_date_1 = request.data.get('start_date_1',
                                            datetime.strftime(default_start_date, '%d/%m/%Y'))
            end_date_1 = request.data.get('end_date_1', datetime.strftime(default_end_date, '%d/%m/%Y'))

            start_date_time = datetime.strptime(start_date_1, '%d/%m/%Y')
            start_date_2 = request.data.get('start_date_2',
                                            datetime.strftime(start_date_time - timedelta(days=365),
                                                              '%d/%m/%Y'))
            end_date_2 = request.data.get('end_date_2',
                                          datetime.strftime(start_date_time - timedelta(days=1),
                                                            '%d/%m/%Y'))

            type_statistic = request.data.get('type_statistic') or request.query_params.get('type_statistic', 'all')

            product_query = request.query_params.get('products', '')
            product_ids = product_query.split(',') if product_query else []

            order_by_field = request.query_params.get('order_by', 'price')

            details_1, details_2 = self.get_order_details(user, start_date_1, end_date_1, start_date_2, end_date_2,
                                                          product_ids, type_statistic)
            statistics, total_statistic = self.calculate_statistics(details_1, details_2)

            sorted_statistics = sorted(statistics.items(),
                                       key=lambda x: x[1].get('current', {}).get(order_by_field, 0),
                                       reverse=True)
            statistics_list = [{"product_id": k, **v} for k, v in sorted_statistics]

            # Get pagination parameters
            limit = int(request.query_params.get('limit', 10))
            page = int(request.query_params.get('page', 1))

            if limit == 0:
                serializer = ProductStatisticsSerializer(statistics_list, many=True)
                response_data = {
                    'total_statistic': total_statistic,
                    'products_statistics': serializer.data,
                    'total_page': 1,
                    'total_count': len(statistics_list),
                    'current_page': 1
                }
                return Response(response_data, status=status.HTTP_200_OK)

            paginator = Paginator(statistics_list, limit)
            page_obj = paginator.get_page(page)
            serializer = ProductStatisticsSerializer(page_obj, many=True)

            response_data = {
                'total_statistic': total_statistic,
                'products_statistics': serializer.data,
                'total_page': paginator.num_pages,
                'total_count': len(statistics_list),
                'current_page': page
            }

            if page < paginator.num_pages:
                next_page = request.build_absolute_uri(
                    f'?page={page + 1}&limit={limit}&user={user_id}&type_statistic={type_statistic}&products={product_query}&start_date_1={start_date_1}&end_date_1={end_date_1}&start_date_2={start_date_2}&end_date_2={end_date_2}&order_by={order_by_field}')
                response_data['next_page'] = next_page
            if page > 1:
                prev_page = request.build_absolute_uri(
                    f'?page={page - 1}&limit={limit}&user={user_id}&type_statistic={type_statistic}&products={product_query}&start_date_1={start_date_1}&end_date_1={end_date_1}&start_date_2={start_date_2}&end_date_2={end_date_2}&order_by={order_by_field}')
                response_data['prev_page'] = prev_page

            return Response(response_data, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            raise e

    def get_order_details(self, user, start_date_1, end_date_1, start_date_2, end_date_2, product_ids, type_statistic):
        start_date_1, end_date_1, start_date_2, end_date_2 = self.convert_dates(start_date_1, end_date_1, start_date_2,
                                                                                end_date_2)

        orders_1 = Order.objects.filter(client_id=user, date_get__gte=start_date_1, date_get__lte=end_date_1)
        orders_2 = Order.objects.filter(client_id=user, date_get__gte=start_date_2, date_get__lte=end_date_2)

        if product_ids:
            orders_1 = orders_1.filter(order_detail__product_id__in=product_ids).distinct()
            orders_2 = orders_2.filter(order_detail__product_id__in=product_ids).distinct()

        match type_statistic:
            case 'special_offer':
                orders_1 = orders_1.filter(Q(new_special_offer__isnull=False) | Q(is_so=True))
                orders_2 = orders_2.filter(Q(new_special_offer__isnull=False) | Q(is_so=True))
            case 'normal':
                orders_1 = orders_1.filter(
                    Q(new_special_offer__isnull=True) & Q(Q(is_so=False) | Q(is_so__isnull=True)))
                orders_2 = orders_2.filter(
                    Q(new_special_offer__isnull=True) & Q(Q(is_so=False) | Q(is_so__isnull=True)))

        details_1 = orders_1.values('order_detail__product_id', 'order_detail__product_id__name').annotate(
            total_quantity=Sum('order_detail__order_quantity'),
            total_point=Sum('order_detail__point_get'),
            total_price=Sum('order_detail__product_price'),
            total_box=Sum('order_detail__order_box'),
            total_cashback=Sum(Case(
                When(order_detail__price_list_so__isnull=False,
                     then=Abs(Coalesce('order_detail__price_list_so', 0.0)) * F('order_detail__order_box')),
                default=0,
                output_field=FloatField()
            ))
        )

        details_2 = orders_2.values('order_detail__product_id', 'order_detail__product_id__name').annotate(
            total_quantity=Sum('order_detail__order_quantity'),
            total_point=Sum('order_detail__point_get'),
            total_price=Sum('order_detail__product_price'),
            total_box=Sum('order_detail__order_box'),
            total_cashback=Sum(Case(
                When(order_detail__price_list_so__isnull=False,
                     then=Abs(Coalesce('order_detail__price_list_so', 0.0)) * F('order_detail__order_box')),
                default=0,
                output_field=FloatField()
            ))
        )

        return details_1, details_2

    def calculate_statistics(self, details_1, details_2):
        combined_results = {}
        total_price = 0
        total_point = 0
        total_cashback = 0
        total_box = 0
        total_products_type = list()
        for detail in details_1:
            product_id = detail['order_detail__product_id']
            product_name = detail['order_detail__product_id__name']
            total_products_type.append(product_id)
            combined_results[product_id] = {
                "product_name": product_name,
                "current": {
                    "price": detail['total_price'] or 0,
                    "point": detail['total_point'] or 0,
                    "quantity": detail['total_quantity'] or 0,
                    "box": detail['total_box'] or 0,
                    "cashback": int(detail['total_cashback'] or 0)
                },
                "total_cashback": int(detail['total_cashback'] or 0)
            }
            total_price += detail['total_price'] or 0
            total_point += detail['total_point'] or 0
            total_cashback += detail['total_cashback'] or 0
            total_box += detail['total_box'] or 0

        total_price_2 = 0
        total_point_2 = 0
        total_cashback_2 = 0
        total_box_2 = 0
        total_products_type2 = list()
        for detail in details_2:
            product_id = detail['order_detail__product_id']
            product_name = detail['order_detail__product_id__name']
            total_products_type2.append(product_id)

            if product_id not in combined_results:
                combined_results[product_id] = {
                    "product_name": product_name,
                    "current": {
                        "price": 0,
                        "point": 0,
                        "quantity": 0,
                        "box": 0,
                        "cashback": 0
                    },
                    "one_year_ago": {}
                }
            first_cashback = combined_results[product_id].get("total_cashback", 0)
            combined_results[product_id]["one_year_ago"] = {
                "price": detail['total_price'] or 0,
                "point": detail['total_point'] or 0,
                "quantity": detail['total_quantity'] or 0,
                "box": detail['total_box'] or 0,
                "cashback": int(detail['total_cashback'] or 0)
            }
            total_price_2 += detail['total_price'] or 0
            total_point_2 += detail['total_point'] or 0
            total_cashback_2 += detail['total_cashback'] or 0
            total_box_2 += detail['total_box'] or 0
            combined_results[product_id]["total_cashback"] = first_cashback + int(detail['total_cashback'] or 0)

        total_statistic = {
            'current': {
                'total_price': total_price, 'total_point': total_point, 'total_cashback': total_cashback,
                'total_box': total_box, 'type_products': len(total_products_type)
            },
            'last_time': {
                'total_price': total_price_2, 'total_point': total_point_2, 'total_cashback': total_cashback_2,
                'total_box': total_box_2, 'type_products': len(total_products_type2)
            }
        }
        return combined_results, total_statistic

    def convert_dates(self, start_date_1, end_date_1, start_date_2, end_date_2):
        start_date_1 = timezone.make_aware(datetime.strptime(start_date_1, '%d/%m/%Y'), timezone.get_current_timezone())
        end_date_1 = timezone.make_aware(
            datetime.strptime(end_date_1, '%d/%m/%Y') + timedelta(days=1) - timedelta(seconds=1),
            timezone.get_current_timezone())

        start_date_2 = timezone.make_aware(datetime.strptime(start_date_2, '%d/%m/%Y'), timezone.get_current_timezone())
        end_date_2 = timezone.make_aware(
            datetime.strptime(end_date_2, '%d/%m/%Y') + timedelta(days=1) - timedelta(seconds=1),
            timezone.get_current_timezone())

        return start_date_1, end_date_1, start_date_2, end_date_2


class OrderReportView(APIView):
    permission_classes = [partial(ValidatePermRest, model=Order)]
    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]

    def get(self, request):
        start_time = time.time()
        data, num_page, current_page, total_count, page_obj, limit = self.get_query_results(request)
        response_data = {
            'data': data,
            'total_page': num_page,
            'current_page': current_page,
            'total_count': total_count
        }
        try:
            if page_obj.has_next():
                next_page = build_absolute_uri_with_params(request,
                                                           {'page': page_obj.next_page_number(), 'limit': limit})
                response_data['next_page'] = next_page

            if page_obj.has_previous():
                prev_page = build_absolute_uri_with_params(request,
                                                           {'page': page_obj.previous_page_number(), 'limit': limit})
                response_data['prev_page'] = prev_page
        except AttributeError:
            pass

        app_log.info(f'OrderReport2 Query Time: {time.time() - start_time}')
        return Response(response_data, status=status.HTTP_200_OK)

    def get_query_results(self, request, get_type_list=False):
        limit = int(request.data.get('limit') or request.query_params.get('limit', 10))
        page = int(request.data.get('page') or request.query_params.get('page', 1))

        orders = handle_order(request)

        client_profiles = {cp.client_id_id: cp for cp in
                           ClientProfile.objects.filter(client_id__in=[o.client_id_id for o in orders])}
        nvtt_ids = set()
        client_lv1_ids = set()
        for o in orders:
            if o.client_id_id in client_profiles:
                if client_profiles[o.client_id_id].nvtt_id:
                    nvtt_ids.add(client_profiles[o.client_id_id].nvtt_id)
                if client_profiles[o.client_id_id].client_lv1_id:
                    client_lv1_ids.add(client_profiles[o.client_id_id].client_lv1_id)
        employee_profiles = {ep.employee_id_id: ep for ep in EmployeeProfile.objects.filter(employee_id__in=nvtt_ids)}
        client_lv1_profiles = {cp.client_id_id: cp for cp in ClientProfile.objects.filter(client_id__in=client_lv1_ids)}

        total_orders = orders.count()
        if limit == 0:
            data = [self.get_order_fields(obj, Order, get_type_list, client_profiles, employee_profiles,
                                          client_lv1_profiles) for obj in orders]
            return data, 1, 1, total_orders, None, limit

        paginator = Paginator(orders, limit)
        page_obj = paginator.get_page(page)
        data = [
            self.get_order_fields(obj, Order, get_type_list, client_profiles, employee_profiles, client_lv1_profiles)
            for obj in page_obj]
        return data, paginator.num_pages, page, total_orders, page_obj, limit

    def get_order_fields(self, obj, model, get_type_list, client_profiles, employee_profiles, client_lv1_profiles):
        order_detail = OrderDetail.objects.filter(order_id=obj)
        client_data = client_profiles.get(obj.client_id_id)
        client_name = client_data.register_name if client_data else None
        nvtt_id = obj.nvtt_id if obj.nvtt_id else (client_data.nvtt_id if client_data else None)

        nvtt = employee_profiles.get(nvtt_id, None)
        nvtt_name = nvtt.register_name if nvtt else None
        client_lv1 = client_lv1_profiles.get(client_data.client_lv1_id) if client_data else None
        client_lv1_name = client_lv1.register_name if client_lv1 else None

        client_info = {
            'id': obj.client_id.id if obj.client_id else '',
            'name': client_name,
            'nvtt': nvtt_name,
            'register_lv1': client_lv1_name
        }
        if get_type_list:
            client_info['list_type'] = obj.list_type

        fields = model._meta.fields
        field_dict = {}
        include_fields = ['id', 'date_get', 'date_company_get', 'date_delay', 'is_so', 'order_point', 'order_price',
                          'note', 'created_at', 'created_by']
        for field in fields:
            field_name = field.name
            if field_name in include_fields:
                include_fields.remove(field_name)
                field_value = getattr(obj, field_name)
                field_dict[field_name] = field_value

        details_fields = OrderDetail._meta.fields
        order_details = []
        for obj in order_detail:
            details_data = {}
            order_details_include = ['product_id', 'order_quantity', 'order_box', 'product_price', 'point_get', 'note']
            for field in details_fields:
                field_name = field.name
                if field_name in order_details_include:
                    field_value = getattr(obj, field_name)
                    if field_name == 'product_id':
                        try:
                            details_data['product_name'] = field_value.name or None
                            field_value = field_value.id
                        except AttributeError:
                            field_value = None
                    details_data[field_name] = field_value
                    order_details_include.remove(field_name)
            order_details.append(details_data)

        field_dict['order_details'] = order_details
        field_dict['clients'] = client_info
        return field_dict


class ApiSeasonalStatisticUser(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                               mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = SeasonStatsUserPointSerializer
    queryset = SeasonalStatisticUser.objects.all()
    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]

    permission_classes = [partial(ValidatePermRest, model=SeasonalStatisticUser)]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        stats_id = request.query_params.get('stats_id', None)
        if stats_id:
            queryset = queryset.filter(season_stats__id=stats_id)
        response = filter_data(self, request,
                               ['id', 'user__id', 'user__username', 'season_stats__id', 'season_stats__name'],
                               queryset=queryset, **kwargs)
        return Response(response, status.HTTP_200_OK)


class ApiSeasonalStatistic(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                           mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = SeasonalStatisticSerializer
    queryset = SeasonalStatistic.objects.all()
    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]

    permission_classes = [partial(ValidatePermRest, model=SeasonalStatistic)]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        stats_type = request.query_params.get('type', None)
        if stats_type:
            queryset = queryset.filter(type=stats_type)

        response = filter_data(self, request, ['id', 'name', 'start_date', 'end_date'],
                               queryset=queryset, **kwargs)
        return Response(response, status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='export')
    def export(self, request, *args, pk=None):
        try:
            season_statistic = self.get_object()
            users_stats = SeasonalStatisticUser.objects.filter(season_stats=season_statistic).values(
                'user__id', 'user__clientprofile__client_lv1_id', 'user__clientprofile__nvtt_id',
                'turn_per_point', 'turn_pick', 'redundant_point', 'total_point'
            )
            df = pd.DataFrame(list(users_stats))

            client_ids = df['user__clientprofile__client_lv1_id']
            nvtt_ids = df['user__clientprofile__nvtt_id']

            client_lv1 = dict(
                ClientProfile.objects.filter(client_id_id__in=client_ids).values_list('client_id', 'register_name'))
            nvtt = dict(
                EmployeeProfile.objects.filter(employee_id_id__in=nvtt_ids).values_list('employee_id', 'register_name'))

            df.rename(columns={
                'user__id': 'Mã Khách Hàng',
                # 'client_lv1_id': 'NPP',
                # 'nvtt_id': 'NVTT',
                'user__clientprofile__client_lv1_id': 'NPP',
                'user__clientprofile__nvtt_id': 'NVTT',
                'turn_per_point': 'Điểm/Tem',
                'turn_pick': 'Số tem',
                'redundant_point': 'Điểm dư',
                'total_point': 'Tổng điểm'
            }, inplace=True)
            df['NPP'] = df['NPP'].map(client_lv1)
            df['NVTT'] = df['NVTT'].map(nvtt)

            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', )
            response['Content-Disposition'] = f'attachment; filename="{season_statistic.name}.xlsx"'
            with pd.ExcelWriter(response, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Season Stats')
                worksheet = writer.sheets['Season Stats']
                # Set column widths (Excel column width units)
                worksheet.column_dimensions['A'].width = 124 / 7  # Approximation to Excel units
                worksheet.column_dimensions['B'].width = 140 / 7
                worksheet.column_dimensions['C'].width = 140 / 7

            return response
        except Exception as e:
            # return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            raise e


class OrderSOCount(APIView):
    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]

    # permission_classes = [partial(ValidatePermRest, model=SeasonalStatistic)]

    def get(self, request):
        today = datetime.today().date()
        user_id = request.query_params.get('user', None)
        so_id = request.query_params.get('so_id', None)
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')
        get_date = request.query_params.get('get_date', f'{today}')

        try:
            user = request.user
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    return Response({'message': f'not found user with id {user_id}'})
            print(f"Test user: {user}")
            base_filter = Q(client_id=user) & Q(new_special_offer__isnull=False)

            if from_date:
                from_date = datetime.strptime(from_date, '%Y-%m-%d')
            if to_date:
                to_date = datetime.strptime(to_date, '%Y-%m-%d')
            if from_date and to_date:
                base_filter &= Q(date_get__gte=from_date, date_get__lte=to_date)
            elif get_date == 'all':
                pass
            else:
                try:
                    get_date = datetime.strptime(get_date, '%Y-%m-%d')
                except ValueError:
                    return Response({'message': "get_date phải có định dạng là 'YYYY-MM-DD' hoặc 'all'"})
                base_filter &= Q(date_get=get_date)
            if so_id:
                base_filter &= Q(new_special_offer__id=so_id)
            get_so_order = Order.objects.filter(base_filter).exclude(
                Q(new_special_offer__type_list=so_type.consider_user))
            order_ids_used = get_so_order.values_list('id', flat=True).distinct()
            so_ids_used = get_so_order.values_list('new_special_offer__id', flat=True).distinct()

            so_objs = SpecialOffer.objects.filter(id__in=list(so_ids_used),
                                                  orders__id__in=list(order_ids_used)).distinct()

            data = self.serializer(so_objs, get_so_order)

            response = {
                'user': {
                    'id': user.id,
                    'register_name': user.clientprofile.register_name
                },
                'data': data,
            }

            return Response(response)
        except Exception as e:
            raise e

    def serializer(self, so_objs, get_so_order):
        data = []
        for so in so_objs:
            orders = get_so_order.filter(new_special_offer=so)
            order_ids = orders.values_list('id', flat=True)
            total_box = OrderDetail.objects.filter(order_id__in=order_ids).aggregate(
                total_box=Sum('order_box'))['total_box'] or 0

            input_data = {
                'so_id': so.id,
                'time_used': orders.count(),
                'total_used_box': total_box,
                'orders_used': list(orders.values_list('id', flat=True)),
            }
            data.append(input_data)
        return data


def handle_order(request) -> QuerySet:
    query, strict_mode, limit, page, order_by, from_date, to_date, date_field = get_query_parameters(request)
    nvtt_query = request.query_params.get('nvtt', '')
    npp_query = request.query_params.get('npp', '')
    daily_query = request.query_params.get('daily', '')

    order_by = '-date_get' if order_by == '' else order_by

    orders = Order.objects.all()

    if from_date or to_date:
        try:
            if from_date:
                from_date = datetime.strptime(from_date, '%d/%m/%Y')
                orders = orders.filter(**{f'{date_field}__gte': from_date})
            if to_date:
                to_date = datetime.strptime(to_date, '%d/%m/%Y') + timedelta(days=1) - timedelta(seconds=1)
                orders = orders.filter(**{f'{date_field}__lte': to_date})
        except ValueError:
            pass

    if nvtt_query and nvtt_query != '':
        nvtt_list = nvtt_query.split(',')
        app_log.info(f'Test nvtt list: {nvtt_list}')
        nvtt_ids = EmployeeProfile.objects.filter(
            Q(register_name__in=nvtt_list) | Q(employee_id__in=nvtt_list)
        ).values_list('employee_id', flat=True)
        client_profile_query = Q(client_id__clientprofile__nvtt_id__in=nvtt_ids)
        orders = orders.filter(client_profile_query)

    if npp_query and npp_query != '':
        npp_list = npp_query.split(',')
        app_log.info(f'Test npp list: {npp_list}')
        npp_ids = ClientProfile.objects.filter(
            Q(register_name__in=npp_list, is_npp=True) | Q(client_id__in=npp_list, is_npp=True)
        ).values_list('client_id', flat=True)
        client_profile_query = Q(client_id__in=npp_ids)
        orders = orders.filter(client_profile_query)

    if daily_query and daily_query != '':
        daily_list = daily_query.split(',')
        exclude_groups = ["NVTT", "TEST", maNhomND]

        daily_ids = ClientProfile.objects.filter(
            Q(register_name__in=daily_list) | Q(client_id__in=daily_list)
        ).exclude(client_group_id__name__in=exclude_groups, is_npp=True).values_list('client_id', flat=True)

        client_query = Q(client_id__in=daily_ids)
        orders = orders.filter(client_query)

    if query != '':
        query_parts = query.split(',')
        order_query = Q()
        order_detail_query = Q()
        client_profile_query = Q()
        for part in query_parts:
            order_query |= Q(id__icontains=part) | Q(date_get__icontains=part) | Q(date_company_get__icontains=part)
            order_detail_query |= Q(order_detail__product_id__id__icontains=part) | Q(
                order_detail__product_id__name__icontains=part)
            client_profile_query |= Q(client_id__clientprofile__register_name__icontains=part) | Q(
                client_id__clientprofile__nvtt_id__icontains=part) | Q(
                client_id__clientprofile__client_group_id__id__icontains=part)

        if strict_mode:
            orders = orders.filter(order_query & order_detail_query & client_profile_query)
        else:
            orders = orders.filter(order_query | order_detail_query | client_profile_query)

    valid_fields = [f.name for f in Order._meta.get_fields()]
    try:
        if order_by in valid_fields or order_by.lstrip('-') in valid_fields:
            orders = orders.order_by(order_by)
        else:
            orders = orders.order_by('created_at')
    except FieldError:
        orders = orders.order_by('id')

    orders = orders.select_related('client_id').prefetch_related(
        Prefetch('order_detail', queryset=OrderDetail.objects.select_related('product_id'))
    )
    return orders


def generate_order_excel(orders):
    workbook = openpyxl.Workbook()
    sheet = workbook.active

    title_font = Font(bold=True, size=20)
    note_font = Font(size=11)
    header_font = Font(bold=True)
    center_alignment = Alignment(horizontal='center', vertical='center')
    header_fill = PatternFill(start_color='FFFF00', end_color='FFFF00', fill_type='solid')

    sheet.merge_cells('A1:N1')
    title_cell = sheet.cell(row=1, column=1)
    title_cell.value = f'Bảng thống kê toa thuốc {datetime.now().strftime("%d-%m-%Y")}'
    title_cell.font = title_font
    title_cell.alignment = center_alignment

    note = f'Ngày thống kê: {datetime.now().strftime("%d/%m/%Y")}   ||   Tổng doanh thu: None   ||   Số lượng bản kê: {orders.count()}'
    sheet.merge_cells('A2:N2')
    note_cell = sheet.cell(row=2, column=1)
    note_cell.value = note
    note_cell.font = note_font
    note_cell.alignment = center_alignment

    columns = [
        'Mã toa',
        'Loại bảng kê', 'Mã khách hàng', 'Tên Khách hàng', 'Khách hàng cấp 1', 'NVTT',
        'Ngày nhận toa', 'Người tạo toa', 'Ngày nhận hàng', 'Ngày gửi trễ', 'Ghi chú',
        'Mã sản phẩm', 'Tên sản phẩm', 'Số lượng', 'Số thùng', 'Thành tiền'
    ]

    column_widths = {
        'Loại bảng kê': 88,
        'Mã khách hàng': 104,
        'Tên Khách hàng': 160,
        'Khách hàng cấp 1': 160,
        'NVTT': 160,
        'Tên sản phẩm': 200,
    }

    for col_num, column_title in enumerate(columns, 1):
        cell = sheet.cell(row=4, column=col_num)  # Thêm tiêu đề cột từ dòng 4
        cell.value = column_title
        cell.font = header_font
        cell.alignment = center_alignment
        cell.fill = header_fill

        col_letter = get_column_letter(col_num)
        if column_title in column_widths:
            sheet.column_dimensions[col_letter].width = column_widths[column_title] / 7.2
        else:
            sheet.column_dimensions[col_letter].width = 120 / 7.2

    row_num = 5

    client_profiles = {cp.client_id_id: cp for cp in
                       ClientProfile.objects.filter(client_id__in=[o.client_id_id for o in orders])}
    client_lv1_ids = [client_profiles[o.client_id_id].client_lv1_id for o in orders if
                      o.client_id_id in client_profiles and client_profiles[o.client_id_id].client_lv1_id]
    client_lv1_profiles = {cp.client_id_id: cp for cp in ClientProfile.objects.filter(client_id__in=client_lv1_ids)}

    nvtt_ids = set()
    for o in orders:
        if o.nvtt_id:
            nvtt_ids.add(o.nvtt_id)
        elif o.client_id_id in client_profiles and client_profiles[o.client_id_id].nvtt_id:
            nvtt_ids.add(client_profiles[o.client_id_id].nvtt_id)
    employee_profiles = {ep.employee_id_id: ep for ep in EmployeeProfile.objects.filter(employee_id__in=nvtt_ids)}

    for i, order in enumerate(orders):
        client_data = client_profiles.get(order.client_id_id)
        try:
            date_send = datetime.strftime(order.date_company_get, "%d/%m/%Y")
        except TypeError:
            date_send = ''
        type_list = order.list_type if order.list_type and order.list_type != '' else 'cấp 2 gửi'

        client_lv1_name = ''
        if client_data and client_data.client_lv1_id in client_lv1_profiles:
            client_lv1_name = client_lv1_profiles[client_data.client_lv1_id].register_name

        nvtt_name = ''
        nvtt_id = order.nvtt_id if order.nvtt_id else (client_data.nvtt_id if client_data else None)
        if nvtt_id and nvtt_id in employee_profiles:
            nvtt_name = employee_profiles[nvtt_id].register_name

        note_dict = {}
        if order.note != '':
            try:
                note_dict = json.loads(order.note)
            except (json.JSONDecodeError, TypeError):
                pass
        noting = note_dict.get('notes', '')
        data_list = [
            order.id,
            type_list,
            client_data.client_id_id if client_data else '',  # Mã khách hàng
            client_data.register_name if client_data else '',  # Tên Khách hàng
            client_lv1_name,  # Khách hàng cấp 1
            nvtt_name,  # NVTT
            order.date_get.strftime("%d/%m/%Y") if order.date_get else '',
            order.created_by,
            date_send,
            order.date_delay if order.date_delay else 0,
            noting,
        ]
        for detail in order.order_detail.all():
            if not detail.product_id:
                continue
            details_data = [
                detail.product_id.id,
                detail.product_id.name,
                detail.order_quantity,
                detail.order_box,
                detail.product_price,
            ]
            export_data = data_list + details_data
            sheet.append(export_data)
            row_num += 1

    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    return output
