from functools import partial

from rest_framework import viewsets, mixins, status
from rest_framework.authentication import BasicAuthentication
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from account.handlers.perms import perm_queryset
from account.handlers.validate_perm import ValidatePermRest
from account.models import User
from marketing.pick_number.api.serializers import UserJoinEventSerializer, EventNumberSerializer, NumberListSerializer, \
    UserJoinEventNumberSerializer
from marketing.pick_number.models import UserJoinEvent, EventNumber, NumberList
from utils.model_filter_paginate import filter_data


class ApiEventNumber(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = EventNumberSerializer
    queryset = EventNumber.objects.all()

    # authentication_classes = [JWTAuthentication, BasicAuthentication]

    # permission_classes = [partial(ValidatePermRest, model=EventNumber)]
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

    # authentication_classes = [JWTAuthentication, BasicAuthentication]

    # permission_classes = [partial(ValidatePermRest, model=UserJoinEvent)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['id', 'event__id', 'event__name', 'user__id'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)


class ApiNumberList(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                    mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = NumberListSerializer
    queryset = NumberList.objects.all()

    # authentication_classes = [JWTAuthentication, BasicAuthentication]

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
