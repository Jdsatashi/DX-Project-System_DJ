from functools import partial

from rest_framework import mixins, viewsets, status
from rest_framework.authentication import BasicAuthentication
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from account.handlers.validate_perm import ValidatePermRest
from marketing.livestream.api.serializers import LiveStreamSerializer, LiveStreamCommentSerializer
from marketing.livestream.models import LiveStream, LiveStreamComment
from utils.model_filter_paginate import filter_data


class ApiLiveStream(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                    mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = LiveStreamSerializer
    queryset = LiveStream.objects.all()

    # authentication_classes = [JWTAuthentication, BasicAuthentication]
    # permission_classes = [partial(ValidatePermRest, model=LiveStream)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['title', 'date_released', 'live_url'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)


class ApiLiveStreamComment(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin):
    serializer_class = LiveStreamCommentSerializer
    queryset = LiveStreamComment.objects.all()

    # authentication_classes = [JWTAuthentication, BasicAuthentication]
    # permission_classes = [partial(ValidatePermRest, model=LiveStreamComment)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['live_stream__title', 'viewers__id', 'comments'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)
