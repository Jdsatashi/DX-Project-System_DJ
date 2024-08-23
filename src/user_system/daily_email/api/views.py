from datetime import datetime
from functools import partial

from rest_framework import mixins, viewsets, status
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from account.handlers.validate_perm import ValidatePermRest
from user_system.daily_email.api.serializers import EmailDetailSerializer, UserGetMailSerializer, \
    SendReportMailSerializer
from user_system.daily_email.models import EmailDetail, UserGetMail
from user_system.daily_email.tasks import send_report_order_email
from utils.model_filter_paginate import filter_data


class ApiEmailDetail(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = EmailDetailSerializer

    queryset = EmailDetail.objects.all()

    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]

    permission_classes = [partial(ValidatePermRest, model=EmailDetail)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['id', 'event__id', 'event__name', 'user__id'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)


class ApiUserGetMail(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = UserGetMailSerializer

    queryset = UserGetMail.objects.all()

    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]

    permission_classes = [partial(ValidatePermRest, model=UserGetMail)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['id', 'event__id', 'event__name', 'user__id'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)


class ApiSendMail(APIView):
    def post(self, request):
        serializer = SendReportMailSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data.get('email')
            date_get = serializer.validated_data.get('date_get', datetime.now().date())

            try:
                send_report_order_email(email, date_get, True)
            except Exception as e:
                raise e
            return Response({'message': 'ok'}, 200)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
