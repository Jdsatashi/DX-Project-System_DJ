from datetime import datetime, time, timedelta

from rest_framework import viewsets, mixins, status
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from app.logs import app_log
from marketing.medias.api.notify.serializers import NotificationSerializer, NotificationUserSerializer
from marketing.medias.models import Notification, NotificationUser
from utils.constants import admin_role
from utils.model_filter_paginate import filter_data


class ApiNotification(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                      mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = NotificationSerializer
    queryset = Notification.objects.all()

    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]

    # permission_classes = [partial(ValidatePermRest, model=User)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['id', 'title'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)


class ApiNotificationUser(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = NotificationUserSerializer
    # queryset = NotificationUser.objects.all()

    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]

    # permission_classes = [partial(ValidatePermRest, model=User)]

    def get_queryset(self):
        user_id = self.kwargs.get('pk', None)
        if user_id:
            return NotificationUser.objects.filter(user__id=user_id)
        else:
            return NotificationUser.objects.all()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        pk = self.kwargs.get('pk', None)
        if pk:
            query_fields = ['notify__id']
        else:
            query_fields = ['notify__id', 'notify__title', 'user__username', 'user__email', 'user__phone__phone_number']
        response = filter_data(self, request, query_fields,
                               queryset=queryset, **kwargs)
        return Response(response, status.HTTP_200_OK)


class TestMail(APIView):
    def get(self, request):
        from app.tasks.report_mail import send_daily_email

        last_date = datetime.today().date() - timedelta(days=1)
        app_log.info(f"Date analysis: {last_date}")
        # - timedelta(days=1)
        emails_param: str = request.query_params.get('emails', 'vdt1073@gmail.com')
        if emails_param in ['', None]:
            emails_param = 'vdt1073@gmail.com'
        emails = emails_param.split(',')
        try:
            send_daily_email(last_date, emails)
            return Response({'message': 'mail sent'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'message': f'error when test mail: {e}'}, status=status.HTTP_400_BAD_REQUEST)
