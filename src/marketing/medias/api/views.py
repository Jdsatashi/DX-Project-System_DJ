from rest_framework import viewsets, mixins, status
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from marketing.medias.api.serializers import NotificationSerializer
from marketing.medias.models import Notification
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
