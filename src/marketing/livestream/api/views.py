from functools import partial

from rest_framework import mixins, viewsets, status
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from account.handlers.validate_perm import ValidatePermRest
from marketing.livestream.api.serializers import LiveStreamSerializer, LiveStreamCommentSerializer, LiveProduct, \
    LiveProductList, LiveStatistic, LiveTracking, LiveStreamDetailCommentSerializer
from marketing.livestream.models import LiveStream, LiveStreamComment, LiveStreamTracking, LiveStreamStatistic, \
    LiveStreamProductList, LiveStreamProduct
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

    authentication_classes = [JWTAuthentication, BasicAuthentication]

    # permission_classes = [partial(ValidatePermRest, model=LiveStreamComment)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['live_stream__title', 'viewers__id', 'comments'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)


class ApiLiveStreamDetailComment(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = LiveStreamDetailCommentSerializer
    queryset = LiveStreamComment.objects.all()

    def list(self, request, *args, **kwargs):
        livestream_id = self.kwargs.get('livestream_id')
        if not livestream_id:
            return Response({'error': 'livestream_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.get_queryset().filter(live_stream_id=livestream_id)
        response = filter_data(self, request, ['comment', 'user__username', 'user__id', 'phone__phone_number'], queryset=queryset)
        return Response(response, status=status.HTTP_200_OK)


class ApiLiveProduct(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = LiveProduct
    queryset = LiveStreamProduct.objects.all()

    authentication_classes = [JWTAuthentication, BasicAuthentication]

    # permission_classes = [partial(ValidatePermRest, model=LiveStreamProduct)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['id', 'product', 'price', 'point', 'live_stream__title'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)


class ApiLiveProductList(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                         mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = LiveProductList
    queryset = LiveStreamProductList.objects.all()

    authentication_classes = [JWTAuthentication, BasicAuthentication]

    # permission_classes = [partial(ValidatePermRest, model=LiveStreamProductList)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['live_stream__title', 'id'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)


class ApiLiveStatistic(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                       mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = LiveStatistic
    queryset = LiveStreamStatistic.objects.all()

    authentication_classes = [JWTAuthentication, BasicAuthentication]

    # permission_classes = [partial(ValidatePermRest, model=LiveStreamStatistic)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['live_stream__title', 'id'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)


class ApiLiveTracking(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                      mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = LiveTracking
    queryset = LiveStreamTracking.objects.all()

    authentication_classes = [JWTAuthentication, BasicAuthentication]

    # permission_classes = [partial(ValidatePermRest, model=LiveStreamTracking)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['live_stream__title', 'phone__phone_number'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)
