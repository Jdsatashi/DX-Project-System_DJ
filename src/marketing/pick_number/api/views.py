from functools import partial
from io import BytesIO

from rest_framework import viewsets, mixins, status
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from account.handlers.perms import perm_queryset
from account.handlers.validate_perm import ValidatePermRest
from account.models import User
from marketing.pick_number.api.serializers import UserJoinEventSerializer, EventNumberSerializer, NumberListSerializer, \
    UserJoinEventNumberSerializer, AwardNumberSerializer, PrizeEventSerializer, PickNumberLogSerializer, \
    AwardUserSerializer
from marketing.pick_number.models import UserJoinEvent, EventNumber, NumberList, PrizeEvent, AwardNumber, PickNumberLog, \
    NumberSelected
from utils.model_filter_paginate import filter_data

from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from django.http import HttpResponse
from openpyxl.styles import Font, Alignment, Border, Side


class ApiEventNumber(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = EventNumberSerializer
    queryset = EventNumber.objects.all()

    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]

    permission_classes = [partial(ValidatePermRest, model=EventNumber)]

    def get_queryset(self):
        user = self.request.user
        return perm_queryset(self, user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        user_id = request.query_params.get('user', None)
        if user_id:
            user = User.objects.filter(id=user_id)
            if not user.exists():
                return Response({'message': f'user id {user_id} not found'})
            user = user.first()
            queryset = perm_queryset(self, user)
        response = filter_data(self, request, ['id', 'name', 'date_start', 'date_close', 'status',
                                               'user_join_event__user__id'], queryset=queryset,
                               **kwargs)
        return Response(response, status.HTTP_200_OK)


class ApiUserJoinEvent(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                       mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = UserJoinEventSerializer
    queryset = UserJoinEvent.objects.all()

    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]

    permission_classes = [partial(ValidatePermRest, model=UserJoinEvent)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['id', 'event__id', 'event__name', 'user__id'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)


class ApiNumberList(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                    mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = NumberListSerializer
    queryset = NumberList.objects.all()

    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]

    # permission_classes = [partial(ValidatePermRest, model=NumberList)]

    def list(self, request, *args, **kwargs):
        active = request.query_params.get('active', 0)
        if active == '1':
            queryset = self.queryset.filter(repeat_count__gt=0)
        elif active == '0':
            queryset = self.queryset.filter(repeat_count=0)
        else:
            queryset = self.queryset
        response = filter_data(self, request, ['id', 'event__id', 'event__name'], queryset=queryset,
                               **kwargs)
        return Response(response, status.HTTP_200_OK)


class ApiPickNumber(viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.UpdateModelMixin):
    serializer_class = UserJoinEventNumberSerializer
    queryset = UserJoinEvent.objects.all()

    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]

    permission_classes = [partial(ValidatePermRest, model=UserJoinEvent)]


class ApiAwardNumber(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = AwardUserSerializer
    queryset = AwardNumber.objects.all()

    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]

    permission_classes = [partial(ValidatePermRest, model=AwardNumber)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request,
                               ['id', 'prize__prize_name', 'prize__event__name', 'prize__prize_id', 'prize__event__id',
                                'number'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)


class ApiPrizeEvent(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                    mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = PrizeEventSerializer
    queryset = PrizeEvent.objects.all()

    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]

    permission_classes = [partial(ValidatePermRest, model=PrizeEvent)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['event__name', 'event__id', 'prize_name', 'note', 'id'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)


class ApiPickNumberLog(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = PickNumberLogSerializer
    queryset = PickNumberLog.objects.all()

    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]

    permission_classes = [partial(ValidatePermRest, model=PickNumberLog)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['event__name', 'event__id', 'user__id',
                                               'user__username', 'user__clientprofile__register_name', 'action'
                                                                                                       'phone__phone_number'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)


class ApiExportEventNumber(APIView):
    def get(self, request, *args, **kwargs):
        event_id = self.kwargs.get('pk')
        event = EventNumber.objects.filter(id=event_id).select_related('table_point').first()
        if event is None:
            return Response({'message': 'event id is required'}, status=400)

        # Tạo workbook và worksheet
        wb = Workbook()
        ws = wb.active
        ws.title = "Báo cáo sự kiện"

        # Định nghĩa font và border
        title_font = Font(size=12, bold=True, underline="single")
        header_font = Font(size=14, bold=True)
        data_font = Font(size=12)
        center_alignment = Alignment(horizontal="center", vertical="center")
        thin_border = Border(left=Side(style='thin'), right=Side(style='thin'),
                             top=Side(style='thin'), bottom=Side(style='thin'))

        # Tạo tiêu đề cho báo cáo
        ws.merge_cells('A1:F1')
        title_cell = ws['A1']
        title_cell.value = f"Báo cáo sự kiện {event.name}"
        title_cell.font = title_font
        # title_cell.alignment = center_alignment

        ws.append([])  # Thêm dòng trống

        # Tạo header
        headers = ["Mã KH", "Số đã chọn"]
        ws.append(headers)

        # Định dạng header
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col_num)
            cell.font = header_font
            cell.alignment = center_alignment
            cell.border = thin_border

        ws.column_dimensions['A'].width = 12.73  # Đặt độ rộng cột "Mã KH"
        ws.column_dimensions['B'].width = 12.73

        # Lấy danh sách user_join_event với prefetch_related cho NumberSelected
        users_join_event = UserJoinEvent.objects.filter(event=event).select_related('user').prefetch_related('number_selected__number')

        row_num = 4  # Bắt đầu từ hàng thứ 4 do tiêu đề và header đã chiếm 3 hàng
        for user_join_event in users_join_event:
            user = user_join_event.user
            selected_numbers = user_join_event.number_selected.all().order_by('created_at')
            turn_pick = user_join_event.turn_pick or 0
            turn_not_pick = turn_pick - selected_numbers.count()

            export_data = [user.id]

            for number_selected in selected_numbers:
                print_data = export_data + [number_selected.number.number]
                self._write_to_sheet(ws, row_num, print_data, data_font, center_alignment, thin_border)
                row_num += 1

            # Thêm các dòng trống nếu có số lần chưa chọn
            for _ in range(turn_not_pick):
                print_data = export_data + ['-']
                self._write_to_sheet(ws, row_num, print_data, data_font, center_alignment, thin_border)
                row_num += 1

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        # Tạo HttpResponse để trả về file Excel
        response = HttpResponse(
            output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename=Bao_cao_su_kien_{event_id}.xlsx'

        return response

    def _write_to_sheet(self, worksheet, row_num, data, font, alignment, border):
        """Helper function to write a row of data to the worksheet with formatting."""
        for col_num, value in enumerate(data, 1):
            cell = worksheet.cell(row=row_num, column=col_num)
            cell.value = value
            cell.font = font
            if col_num == 2:  # Căn giữa cột "Số đã chọn"
                cell.alignment = alignment
            cell.border = border


class ApiUserAward(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = AwardUserSerializer
    queryset = AwardNumber.objects.all()

    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]

    permission_classes = [partial(ValidatePermRest, model=PickNumberLog)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['number'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)
