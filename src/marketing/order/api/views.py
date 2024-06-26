import time
from datetime import datetime, timedelta
from functools import partial

import openpyxl
from django.core.exceptions import FieldError
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from django.http import HttpResponse
from django.utils import timezone
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
from rest_framework import viewsets, mixins, status
from rest_framework.authentication import BasicAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from account.handlers.perms import DataFKModel
from account.handlers.validate_perm import ValidatePermRest
from account.models import User
from app.logs import app_log
from marketing.order.api.serializers import OrderSerializer, ProductStatisticsSerializer
from marketing.order.models import Order, OrderDetail
from marketing.price_list.models import SpecialOfferProduct
from user_system.client_profile.models import ClientProfile
from user_system.employee_profile.models import EmployeeProfile
from utils.constants import maNhomND
from utils.model_filter_paginate import filter_data, get_query_parameters


class GenericApiOrder(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                      mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = OrderSerializer
    queryset = Order.objects.all()
    authentication_classes = [JWTAuthentication, BasicAuthentication]

    permission_classes = [partial(ValidatePermRest, model=Order)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['id', 'date_get', 'date_company_get', 'client_id__id'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)

    def users_order(self, request, *args, **kwargs):
        user_id = request.query_params.get('user', None)
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
    serializer_class = ProductStatisticsSerializer

    def get(self, request, *args, **kwargs):
        try:
            # Get current user
            user_id = request.query_params.get('user', '')
            if user_id == '':
                user = request.user
            else:
                current_user = request.user
                user = User.objects.filter(id=user_id.upper()).first()
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

            type_statistic = request.data.get('type_statistic', 'all')
            input_date = {'start_date_1': start_date_1, 'end_date_1': end_date_1,
                          'start_date_2': start_date_2, 'end_date_2': end_date_2}

            nvtt_query = request.query_params.get('nvtt', '')
            npp_query = request.query_params.get('npp', '')
            daily_query = request.query_params.get('daily', '')
            query = {'nvtt': nvtt_query, 'npp': npp_query, 'daily': daily_query}
            # Get param variables data
            limit = request.query_params.get('limit', 10)
            page = int(request.query_params.get('page', 1))

            # Data set for statistic
            statistics = get_product_statistics(user, input_date, query, type_statistic)

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
            raise e
            # return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ExportReport(APIView):
    permission_classes = [partial(ValidatePermRest, model=Order)]

    def get(self, request):
        # Get data from OrderReport
        limit = request.query_params.get('limit', 10)
        response_data, _, _ = OrderReportView().get_query_results(request)

        # Add new workbook
        workbook = openpyxl.Workbook()
        sheet = workbook.active

        # Format title
        title_font = Font(bold=True, size=20)
        note_font = Font(size=11)
        header_font = Font(bold=True)
        center_alignment = Alignment(horizontal='center', vertical='center')
        header_fill = PatternFill(start_color='FFFF00', end_color='FFFF00', fill_type='solid')

        # Create Title
        sheet.merge_cells('A1:N1')
        title_cell = sheet.cell(row=1, column=1)
        title_cell.value = f'Bảng thống kê toa thuốc {datetime.now().strftime("%d/%m/%Y")}'
        title_cell.font = title_font
        title_cell.alignment = center_alignment

        # Suport note
        note = f'Ngày thống kê: {datetime.now().strftime("%d/%m/%Y")}   ||   Tổng doanh thu: None   ||   Số lượng bản kê: {limit}'
        sheet.merge_cells('A2:N2')
        note_cell = sheet.cell(row=2, column=1)
        note_cell.value = note
        note_cell.font = note_font
        note_cell.alignment = center_alignment

        # Tiêu đề cột
        columns = [
            'Loại bảng kê', 'Mã khách hàng', 'Tên Khách hàng', 'Khách hàng cấp 1', 'NVTT',
            'Ngày nhận toa', 'Ngày nhận hàng', 'Ngày gửi trễ', 'Ghi chú',
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

            # Đặt độ rộng cột
            col_letter = get_column_letter(col_num)
            if column_title in column_widths:
                sheet.column_dimensions[col_letter].width = column_widths[
                                                                column_title] / 7.2  # Chia để chuyển đổi từ px sang độ rộng cột
            else:
                sheet.column_dimensions[col_letter].width = 120 / 7.2  # Đặt độ rộng cột mặc định

        # Thêm dữ liệu vào sheet
        row_num = 5  # Bắt đầu thêm dữ liệu từ dòng 5
        for order in response_data:
            for detail in order['order_details']:
                product_price = detail['product_price'] or 0
                try:
                    date_send = datetime.strftime(order['date_company_get'], "%d/%m/%Y")
                except TypeError:
                    date_send = ''
                if order.get('clients') is None:
                    order['client'] = {
                        'id': None,
                        'name': None,
                        'register_lv1': None,
                        'nvtt': None
                    }
                sheet.append([
                    '',
                    order['clients']['id'],
                    order['clients']['name'],
                    order['clients']['register_lv1'],
                    order['clients']['nvtt'],
                    order['date_get'],
                    date_send,
                    order['date_delay'],
                    order['note'],
                    detail['product_id'],
                    detail['product_name'],
                    detail['order_quantity'],
                    detail['order_box'],
                    product_price,
                ])
                row_num += 1

        # Tạo response với Content-Disposition để tải xuống tệp Excel
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=orders.xlsx'

        # Lưu workbook vào response
        workbook.save(response)

        return response


class OrderReportView(APIView):
    permission_classes = [partial(ValidatePermRest, model=Order)]

    def get(self, request):
        start_time = time.time()

        data, total_pages, current_page = self.get_query_results(request)

        # Add total and current page and data to response data
        response_data = {
            'data': data,
            'total_page': total_pages,
            'current_page': current_page
        }
        app_log.info(f'OrderReport2 Query Time: {time.time() - start_time}')
        return Response(response_data, status=status.HTTP_200_OK)

    def get_query_results(self, request):
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
            # include_group = GroupPerm.objects.filter(name__icontains='client').values_list('name', flat=True)
            # daily_ids = ClientProfile.objects.filter(
            #     Q(register_name__in=daily_list) | Q(client_id__in=daily_list),
            #     client_id__group_user__name__in=list(include_group)
            # ).exclude(is_npp=True).values_list('client_id', flat=True)
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

        # Get fields in models
        valid_fields = [f.name for f in Order._meta.get_fields()]
        # Check field order_by exists, then order queryset
        try:
            if order_by in valid_fields or order_by.lstrip('-') in valid_fields:
                orders = orders.order_by(order_by)
            else:
                try:
                    orders = orders.order_by('created_at')
                except FieldError:
                    orders = orders.order_by('id')
                except Exception as e:
                    app_log.error(f"Error order_by fields")
                    return Response({'message': 'error field order_by not in model'}, status=200)
        except FieldError:
            pass
        if limit == 0:
            data = [self.get_order_fields(obj, Order) for obj in orders]
            return data, 1, 1
        paginator = Paginator(orders, limit)
        page_obj = paginator.get_page(page)

        # Validate page number
        if page < 0:
            page = 1
        elif page > paginator.num_pages:
            page = paginator.num_pages

        data = [self.get_order_fields(obj, Order) for obj in page_obj]
        return data, paginator.num_pages, page

    def get_order_fields(self, obj, model):
        order_detail = OrderDetail.objects.filter(order_id=obj)
        try:
            client_profile = ClientProfile.objects.get(client_id=obj.client_id)
            client_name = client_profile.register_name
            nvtt = EmployeeProfile.objects.filter(employee_id=client_profile.nvtt_id).first()

            if not nvtt:
                nvtt_name = None
            else:
                nvtt_name = nvtt.register_name

            client_lv1 = ClientProfile.objects.filter(client_id=client_profile.client_lv1_id).first()
            if not client_lv1:
                client_lv1_name = None
            else:
                client_lv1_name = client_lv1.register_name

            client_data = {
                'id': obj.client_id.id,
                'name': client_name,
                'nvtt': nvtt_name,
                'register_lv1': client_lv1_name
            }
        except ClientProfile.DoesNotExist:
            app_log.info(f"Error user '{obj.client_id}' not has profile")
            client_data = None

        fields = model._meta.fields
        field_dict = {}
        include_fields = ['id', 'date_get', 'date_company_get', 'date_delay', 'id_offer_consider',
                          'order_point', 'order_price', 'note', 'created_at']
        # fk_field = DataFKModel(model)
        # fk_fields = fk_field.get_fk_fields()
        for field in fields:
            field_name = field.name
            if field_name in include_fields:
                # if field_name not in fk_fields:
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
        # field_dict['order_details'] = [self.get_object_fields_exclude_fk(obj2, OrderDetail) for obj2 in order_detail]
        # field_dict = Order3Serializer(obj).data
        # field_dict['order_details'] = OrderDetail3Serializer(order_detail, many=True).data
        field_dict['order_details'] = order_details
        field_dict['clients'] = client_data
        return field_dict

    @staticmethod
    def get_object_fields_exclude_fk(obj, model):
        fields = model._meta.fields
        field_dict = {}
        fk_field = DataFKModel(model)
        fk_fields = fk_field.get_fk_fields()
        for field in fields:
            field_name = field.name
            if field_name not in fk_fields:
                field_value = getattr(obj, field_name)
                field_dict[field_name] = field_value
            else:
                fk_fields.remove(field_name)
        return field_dict


def get_product_statistics(user, input_date, query, type_statistic):
    app_log.info(f"User id: {user}")
    # Convert date format
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

    # Get orders for each date range
    orders_1 = Order.objects.filter(client_id=user, date_get__gte=start_date_1, date_get__lte=end_date_1)
    orders_2 = Order.objects.filter(client_id=user, date_get__gte=start_date_2, date_get__lte=end_date_2)

    # Apply query filters
    # if query.get('nvtt') != '':
    #     nvtt_list = query.get('nvtt').split(',')
    #     nvtt_ids = EmployeeProfile.objects.filter(
    #         (Q(register_name__in=nvtt_list) | Q(employee_id__in=nvtt_list)) & Q(employee_id__group_user__name="nvtt")
    #     ).values_list('employee_id', flat=True)
    #     client_profile_query = Q(client_id__clientprofile__nvtt_id__in=nvtt_ids)
    #     orders_1 = orders_1.filter(client_profile_query)
    #     orders_2 = orders_2.filter(client_profile_query)
    #
    # if query.get('npp') != '':
    #     npp_list = query.get('npp').split(',')
    #     npp_ids = ClientProfile.objects.filter(
    #         (Q(register_name__in=npp_list, is_npp=True) | Q(client_id__in=npp_list, is_npp=True)) &
    #         Q(client_id__group_user__name="npp")
    #     ).values_list('client_id', flat=True)
    #     client_profile_query = Q(client_id__in=npp_ids)
    #     orders_1 = orders_1.filter(client_profile_query)
    #     orders_2 = orders_2.filter(client_profile_query)
    #
    # if query.get('daily') != '':
    #     daily_list = query.get('daily').split(',')
    #     exclude_groups = ["NVTT", "TEST", maNhomND]
    #     daily_ids = ClientProfile.objects.filter(
    #         Q(register_name__in=daily_list) | Q(client_id__in=daily_list)
    #     ).exclude(client_group_id__name__in=exclude_groups, is_npp=True).values_list('client_id', flat=True)
    #     client_query = Q(client_id__in=daily_ids)
    #     orders_1 = orders_1.filter(client_query)
    #     orders_2 = orders_2.filter(client_query)

    # Get orders for each date range with type_statistic
    match type_statistic:
        case 'special_offer':
            orders_1 = orders_1.filter(Q(new_special_offer__isnull=False) | Q(is_so=True))
            orders_2 = orders_2.filter(Q(new_special_offer__isnull=False) | Q(is_so=True))
        case 'normal':
            orders_1 = orders_1.filter(Q(new_special_offer__isnull=True) & Q(is_so=False))
            orders_2 = orders_2.filter(Q(new_special_offer__isnull=True) & Q(is_so=False))

    # Get order details for each date range
    details_1 = OrderDetail.objects.filter(order_id__in=orders_1).values('product_id', 'product_id__name').annotate(
        total_quantity=Sum('order_quantity'),
        total_point=Sum('point_get'),
        total_price=Sum('product_price'),
        total_box=Sum('order_box')
    )

    details_2 = OrderDetail.objects.filter(order_id__in=orders_2).values('product_id', 'product_id__name').annotate(
        total_quantity=Sum('order_quantity'),
        total_point=Sum('point_get'),
        total_price=Sum('product_price'),
        total_box=Sum('order_box')
    )

    # Combine results into a single dictionary
    combined_results = {}
    for detail in details_1:
        app_log.info("- - - - - ")
        app_log.info(f"Test detail: {detail}")
        product_id = detail['product_id']
        product_name = detail['product_id__name']
        total_cashback = 0

        # Calculate total cashback for current period
        for order in orders_1:
            app_log.info("----------")
            app_log.info(f"Test product_id: {product_id}")
            order_detail = OrderDetail.objects.filter(order_id=order, product_id=product_id).first()
            special_offer = order.new_special_offer
            app_log.info(f"Test order: {order}")
            if special_offer and order_detail:
                sop = SpecialOfferProduct.objects.filter(special_offer=special_offer, product_id=product_id).first()
                if sop and sop.cashback:
                    app_log.info(f"Test sop: {sop}")
                    app_log.info(f"Test order_detail: {order_detail}")
                    total_cashback += sop.cashback * order_detail.order_box

        combined_results[product_id] = {
            "product_name": product_name,
            "current": {
                "price": detail['total_price'],
                "point": detail['total_point'],
                "quantity": detail['total_quantity'],
                "box": detail['total_box']
            },
            "total_cashback": total_cashback
        }
        app_log.info(f"Test cashback details 1: {total_cashback}")
    for detail in details_2:
        product_id = detail['product_id']
        product_name = detail['product_id__name']
        total_cashback = 0

        if product_id not in combined_results:
            combined_results[product_id] = {
                "product_name": product_name,
                "one_year_ago": {}
            }

        # Calculate total cashback for previous period
        for order in orders_2:
            order_detail = OrderDetail.objects.filter(order_id=order, product_id=product_id).first()
            special_offer = order.new_special_offer
            if special_offer and order_detail:
                sop = SpecialOfferProduct.objects.filter(special_offer=special_offer, product_id=product_id).first()
                if sop and sop.cashback:
                    total_cashback += sop.cashback * order_detail.order_box

        combined_results[product_id]["one_year_ago"] = {
            "price": detail['total_price'],
            "point": detail['total_point'],
            "quantity": detail['total_quantity'],
            "box": detail['total_box']
        }
        combined_results[product_id]["total_cashback"] = total_cashback
        app_log.info(f"Test cashback details 2: {total_cashback}")

    return combined_results
