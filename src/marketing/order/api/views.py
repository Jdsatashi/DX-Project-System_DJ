from datetime import datetime, timedelta
from functools import partial

from django.core.paginator import Paginator
from django.db.models import Sum
from django.utils import timezone
from rest_framework import viewsets, mixins, status
from rest_framework.authentication import BasicAuthentication
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from account.handlers.validate_perm import ValidatePermRest
from marketing.order.api.serializers import OrderSerializer, ProductStatisticsSerializer
from marketing.order.models import Order, OrderDetail
from utils.model_filter_paginate import filter_data


class GenericApiOrder(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                      mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = OrderSerializer
    queryset = Order.objects.all()
    authentication_classes = [JWTAuthentication, BasicAuthentication]

    # permission_classes = [partial(ValidatePermRest, model=Order)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['id', 'date_get', 'date_company_get', 'client_id'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)

    def users_order(self, request, *args, **kwargs):
        user = self.request.user
        print(f"User test: {user}")
        orders = Order.objects.filter(client_id=user)
        response = filter_data(self, request, ['id', 'date_get', 'date_company_get', 'client_id'], queryset=orders,
                               **kwargs)
        return Response(response, status.HTTP_200_OK)


class ProductStatisticsView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            # Get current user
            user = request.user
            now = datetime.now().date()
            # Set date default
            default_start_date = now - timedelta(days=365)
            default_end_date = now

            start_date_1 = request.data.get('start_date_1', datetime.strftime(default_start_date, '%d/%m/%Y'))
            end_date_1 = request.data.get('end_date_1', datetime.strftime(default_end_date, '%d/%m/%Y'))

            start_date_time = datetime.strptime(start_date_1, '%d/%m/%Y')
            start_date_2 = request.data.get('start_date_2', datetime.strftime(start_date_time - timedelta(days=365), '%d/%m/%Y'))
            end_date_2 = request.data.get('end_date_2', datetime.strftime(start_date_time - timedelta(days=1), '%d/%m/%Y'))

            # Get param variables data
            limit = request.query_params.get('limit', 10)
            page = int(request.query_params.get('page', 1))

            # Data set for statistic
            statistics = get_product_statistics_2(user, start_date_1, end_date_1, start_date_2, end_date_2)

            statistics_list = [{"product_id": k, "data": v} for k, v in statistics.items()]

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
                'current_page': page
            }
            if page_obj.has_next():
                next_page = request.build_absolute_uri(
                    '?page={}&limit={}'.format(
                        page_obj.next_page_number(), limit))
                response_data['next_page'] = next_page
            # If has previous page, add urls to response data
            if page_obj.has_previous():
                prev_page = request.build_absolute_uri(
                    '?page={}&limit={}'.format(
                        page_obj.previous_page_number(), limit))
                response_data['prev_page'] = prev_page
            return Response(response_data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            # return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


def get_product_statistics(user, start_date, end_date):
    # Convert date format
    start_date = datetime.strptime(start_date, '%d/%m/%Y')
    end_date = datetime.strptime(end_date, '%d/%m/%Y') + timedelta(days=1) - timedelta(seconds=1)
    start_date = timezone.make_aware(start_date, timezone.get_current_timezone())
    end_date = timezone.make_aware(end_date, timezone.get_current_timezone())
    print()
    # Lấy tất cả các Order của user hiện tại trong khoảng thời gian đã cho
    orders = Order.objects.filter(client_id=user, created_at__gte=start_date, created_at__lte=end_date)
    print(f"Query order: {orders}")

    # Lấy tất cả OrderDetail liên quan đến các Order đã lọc
    return OrderDetail.objects.filter(
        order_id__in=orders
    ).values('product_id').annotate(
        total_quantity=Sum('order_quantity'),
        total_point=Sum('point_get'),
        total_price=Sum('product_price')
    ).order_by('product_id')


def get_product_statistics_2(user, start_date_1, end_date_1, start_date_2, end_date_2):
    # Convert date format
    start_date_1 = timezone.make_aware(datetime.strptime(start_date_1, '%d/%m/%Y'), timezone.get_current_timezone())
    end_date_1 = timezone.make_aware(datetime.strptime(end_date_1, '%d/%m/%Y') + timedelta(days=1) - timedelta(seconds=1), timezone.get_current_timezone())

    start_date_2 = timezone.make_aware(datetime.strptime(start_date_2, '%d/%m/%Y'), timezone.get_current_timezone())
    end_date_2 = timezone.make_aware(datetime.strptime(end_date_2, '%d/%m/%Y') + timedelta(days=1) - timedelta(seconds=1), timezone.get_current_timezone())

    # Get orders for each date range
    orders_1 = Order.objects.filter(client_id=user, created_at__gte=start_date_1, created_at__lte=end_date_1)
    orders_2 = Order.objects.filter(client_id=user, created_at__gte=start_date_2, created_at__lte=end_date_2)

    # Get order details for each date range
    details_1 = OrderDetail.objects.filter(order_id__in=orders_1).values('product_id').annotate(
        total_quantity=Sum('order_quantity'),
        total_point=Sum('point_get'),
        total_price=Sum('product_price')
    )

    details_2 = OrderDetail.objects.filter(order_id__in=orders_2).values('product_id').annotate(
        total_quantity=Sum('order_quantity'),
        total_point=Sum('point_get'),
        total_price=Sum('product_price')
    )

    # Combine results into a single dictionary
    combined_results = {}
    for detail in details_1:
        product_id = detail['product_id']
        combined_results[product_id] = {
            f"current": {
                "price": detail['total_price'],
                "point": detail['total_point'],
                "quantity": detail['total_quantity']
            }
        }

    for detail in details_2:
        product_id = detail['product_id']
        if product_id not in combined_results:
            combined_results[product_id] = {}
        combined_results[product_id][f"one_year_ago"] = {
            "price": detail['total_price'],
            "point": detail['total_point'],
            "quantity": detail['total_quantity']
        }

    return combined_results
