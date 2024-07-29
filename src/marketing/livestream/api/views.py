from functools import partial

from django.shortcuts import get_object_or_404
from rest_framework import mixins, viewsets, status
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from account.handlers.perms import perm_queryset
from account.handlers.validate_perm import ValidatePermRest
from account.models import PhoneNumber
from app.logs import app_log
from marketing.livestream.api.serializers import LiveStreamSerializer, LiveStreamCommentSerializer, \
    LiveStatistic, LiveTracking, LiveStreamDetailCommentSerializer, PeekViewSerializer, LiveOfferRegisterSerializer
from marketing.livestream.models import LiveStream, LiveStreamComment, LiveStreamTracking, LiveStreamStatistic, \
    LiveStreamPeekView, LiveStreamOfferRegister
from utils.model_filter_paginate import filter_data


class ApiLiveStream(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                    mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = LiveStreamSerializer
    queryset = LiveStream.objects.all()

    authentication_classes = [JWTAuthentication, BasicAuthentication]
    permission_classes = [partial(ValidatePermRest, model=LiveStream)]

    def get_queryset(self):
        return perm_queryset(self)

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['title', 'date_released', 'live_url'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)


class ApiLiveStreamComment(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin):
    serializer_class = LiveStreamCommentSerializer
    queryset = LiveStreamComment.objects.all()

    authentication_classes = [JWTAuthentication, BasicAuthentication]

    permission_classes = [partial(ValidatePermRest, model=LiveStreamComment)]

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
        response = filter_data(self, request, ['comment', 'user__username', 'user__id', 'phone__phone_number'],
                               queryset=queryset)
        return Response(response, status=status.HTTP_200_OK)


# class ApiLiveProduct(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
#                      mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
#     serializer_class = LiveProduct
#     queryset = LiveStreamProduct.objects.all()
#
#     authentication_classes = [JWTAuthentication, BasicAuthentication]
#
#     # permission_classes = [partial(ValidatePermRest, model=LiveStreamProduct)]
#
#     def list(self, request, *args, **kwargs):
#         response = filter_data(self, request, ['id', 'product', 'price', 'point', 'live_stream__title'],
#                                **kwargs)
#         return Response(response, status.HTTP_200_OK)
#
#
# class ApiLiveProductList(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
#                          mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
#     serializer_class = LiveProductList
#     queryset = LiveStreamProductList.objects.all()
#
#     authentication_classes = [JWTAuthentication, BasicAuthentication]
#
#     # permission_classes = [partial(ValidatePermRest, model=LiveStreamProductList)]
#
#     def list(self, request, *args, **kwargs):
#         response = filter_data(self, request, ['live_stream__title', 'id'],
#                                **kwargs)
#         return Response(response, status.HTTP_200_OK)


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


#
#
# class ApiLiveOrder(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
#                    mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
#     serializer_class = LiveOrderSerializer
#     queryset = OrderLiveProduct.objects.all()
#
#     authentication_classes = [JWTAuthentication, BasicAuthentication]
#
#     # permission_classes = [partial(ValidatePermRest, model=LiveStreamTracking)]
#
#     def list(self, request, *args, **kwargs):
#         response = filter_data(self, request,
#                                ['livestream_product_list__title', 'livestream_product_list__id', 'phone__phone_number'],
#                                **kwargs)
#         return Response(response, status.HTTP_200_OK)


class ApiPeekView(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = PeekViewSerializer
    queryset = LiveStreamPeekView.objects.all()

    authentication_classes = [JWTAuthentication, BasicAuthentication]

    # permission_classes = [partial(ValidatePermRest, model=LiveStreamComment)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['live_stream__id'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)


class JoinPeekView(APIView):
    def post(self, request, *args, **kwargs):
        live_stream_id = request.data.get('live_stream_id')
        livestream = LiveStream.objects.filter(id=live_stream_id).first()
        app_log.info(livestream)
        peek_view = LiveStreamPeekView.objects.filter(live_stream=livestream).first()
        app_log.info(peek_view)
        peek_view.in_livestream += 1
        peek_view.save()
        return Response(PeekViewSerializer(peek_view).data, status=status.HTTP_200_OK)


class LeavePeekView(APIView):
    def post(self, request, *args, **kwargs):
        live_stream_id = request.data.get('live_stream_id')
        livestream = LiveStream.objects.filter(id=live_stream_id).first()
        peek_view = LiveStreamPeekView.objects.filter(live_stream=livestream).first()
        app_log.info(peek_view)
        peek_view.out_livestream += 1
        peek_view.save()
        return Response(PeekViewSerializer(peek_view).data, status=status.HTTP_200_OK)


class ApiLiveOfferRegister(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                           mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = LiveOfferRegisterSerializer
    queryset = LiveStreamOfferRegister.objects.all()

    authentication_classes = [JWTAuthentication, BasicAuthentication]

    # permission_classes = [partial(ValidatePermRest, model=LiveStreamComment)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['live_stream__title', 'live_stream__id', 'phone__phone_number'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)


class CheckLiveStreamRegistrationView(APIView):
    def post(self, request, *args, **kwargs):
        live_stream_id = request.data.get('live_stream_id')
        phone_number = request.data.get('phone_number')

        if not live_stream_id or not phone_number:
            return Response({'error': 'live_stream_id and phone_number are required'},
                            status=status.HTTP_400_BAD_REQUEST)

        live_stream = get_object_or_404(LiveStream, id=live_stream_id)
        phone = get_object_or_404(PhoneNumber, phone_number=phone_number)
        user = phone.user

        # Kiểm tra tất cả các số điện thoại của người dùng
        phone_numbers = PhoneNumber.objects.filter(user=user)

        registered = LiveStreamOfferRegister.objects.filter(live_stream=live_stream, phone__in=phone_numbers,
                                                            register=True).exists()

        if registered:
            return Response({'register': True}, status=status.HTTP_200_OK)
        else:
            return Response({'register': False},
                            status=status.HTTP_200_OK)
