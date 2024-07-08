from django.core.mail import send_mail
from rest_framework import viewsets, mixins, status
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from app import settings
from app.logs import app_log
from marketing.medias.api.notify.serializers import NotificationSerializer, NotificationUserSerializer
from marketing.medias.models import Notification, NotificationUser
from utils.env import EMAIL_SENDER, EMAIL_SENDER_NAME
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
        subject = 'Thank you for registering to our site'
        message = ' it  means a world to us '
        email_from = ''
        if EMAIL_SENDER_NAME:
            email_from = EMAIL_SENDER_NAME

        if email_from == EMAIL_SENDER_NAME and EMAIL_SENDER:
            email_from += f" <{EMAIL_SENDER}>"
        elif EMAIL_SENDER:
            email_from = EMAIL_SENDER
        else:
            email_from = settings.EMAIL_HOST_USER
        app_log.info(f"Test sender: {email_from}")
        recipient_list = ['jdsatashi@gmail.com',]
        send_mail(subject, message, email_from, recipient_list)
        return Response({'message': 'mail sent'}, status.HTTP_200_OK)
