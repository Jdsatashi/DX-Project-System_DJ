from functools import partial

import requests
from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import mixins, viewsets, status
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken as RestRefreshToken

from account.api.serializers import UserSerializer, RegisterSerializer, create_verify_code
from account.handlers.handle import handle_create_acc
from account.handlers.validate_perm import ValidatePermRest
from account.models import User, Verify, PhoneNumber, RefreshToken
from app.api_routes.handlers import get_token_for_user, remove_token_blacklist
from utils.constants import status as user_status
from utils.env import APP_SERVER
from utils.helpers import generate_digits_code
from utils.model_filter_paginate import filter_data


def api_create_user(req):
    ctx = handle_create_acc(req)
    return HttpResponse(ctx, content_type='application/json')


# Register api view
class ApiAccount(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                 mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [partial(ValidatePermRest, model=User)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['id', 'username', 'email', 'phone_numbers__phone_number'], *args,
                               **kwargs)
        return Response(response, status.HTTP_200_OK)


class RegisterSMS(APIView):
    authentication_classes = [JWTAuthentication, BasicAuthentication]

    # permission_classes = [partial(ValidatePermRest, model=User)]

    def get_serializer(self, *args, **kwargs):
        return RegisterSerializer(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(data={
            'phone_number': '',
        })
        return Response(serializer.initial_data)

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.save()
            return Response(result, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST', 'GET'])
def otp_verify(request, pk):
    if request.method == 'GET':
        response = {
            'otp_code': '123456'
        }
        return Response(response, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    try:
        phone = PhoneNumber.objects.get(phone_number=pk)
    except PhoneNumber.DoesNotExist:
        return HttpResponse(status=status.HTTP_404_NOT_FOUND)
    if request.method == 'POST':
        otp_code = request.data.get('otp_code', None)
        verify = Verify.objects.filter(phone_verify=phone).latest('created_at')
        print(f"-------------TEST--------------")
        print(otp_code)
        print(verify)
        if verify.is_verify:
            return Response({'message': 'Tài khoản đã xác thực.'}, status=status.HTTP_400_BAD_REQUEST)
        if otp_code != verify.verify_code:
            return Response({'message': 'Mã OTP không chính xác.'}, status=status.HTTP_400_BAD_REQUEST)
        if verify.is_verify_valid():
            # Update verify
            verify.is_verify = True
            verify.verify_time = timezone.now()
            # Activate user
            verify.user.status = user_status[0]
            verify.user.is_active = True
            verify.user.save()
            verify.save()
            # Generate new token
            token = get_token_for_user(verify.user)
            # Add data for refresh token
            active_token = RefreshToken.objects.filter(user=verify.user, status="active")
            if active_token.exists():
                token_obj = active_token.first()
                token_obj.status = "deactivate"
                token_obj.save()
                _token = RestRefreshToken(token_obj.refresh_token)
                _token.blacklist()
            ref_token = RefreshToken.objects.create(user=verify.user, phone_number=phone,
                                                    refresh_token=str(token['refresh']), status="active")
            verify.refresh_token = ref_token
            verify.save()
            # Add response data
            serializer = UserSerializer(verify.user)
            response = {'message': 'Successful verify phone number', 'user': serializer.data, 'phone_number': pk,
                        'token': {
                            'refresh': str(token['refresh']),
                            'access': str(token['access'])
                        }}
            return Response(response, status=status.HTTP_200_OK)
        print("OTP code is expired")
        return Response({'message': 'Mã otp đã hết hạn'}, status=status.HTTP_200_OK)

    return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST', 'GET'])
def phone_login(request):
    if request.method == 'POST':
        phone_number = request.data.get('phone_number', None)
        refresh_token = request.data.get('refresh_token', None)
        if phone_number is None:
            return Response({'message': 'Bạn cần nhập số điện thoại'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            phone = PhoneNumber.objects.get(phone_number=phone_number)
        except PhoneNumber.DoesNotExist:
            response_data = call_api_register(phone_number)
            return Response(response_data)

        user = phone.user
        if refresh_token:
            ref_token = RefreshToken.objects.filter(refresh_token=refresh_token, phone_number=phone)
            if ref_token.exists():
                print("test 1")
                if ref_token.first().status == "deactivate":
                    print("Here test 3")
                    remove_token_blacklist(refresh_token)
                    current_token = ref_token.first()
                    current_token.status = "active"
                    current_token.save()
                try:
                    new_token = get_token_from_refresh(refresh_token)
                except TokenError:
                    return Response({'message': 'Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại'}, status.HTTP_400_BAD_REQUEST)
                return Response({'refresh': refresh_token, 'access': new_token}, status.HTTP_200_OK)
            return Response({'message': 'Token không tồn tại'}, status.HTTP_400_BAD_REQUEST)
        else:
            print("test 2")
            verify_code = generate_digits_code()
            new_verify = Verify.objects.create(user=user, phone_verify=phone, verify_code=verify_code,
                                               verify_type="SMS OTP")
            response = create_verify_code(new_verify)
            return Response(response, status.HTTP_200_OK)
    else:
        response = {
            'phone_number': '0123456789',
            'refresh_token': 'token...'
        }
        return Response(response, status=status.HTTP_405_METHOD_NOT_ALLOWED)


def call_api_register(phone_number):
    # Get path
    main_url = APP_SERVER
    register_path = f"/application/api/v1/2024/accounts/register/"
    api_url = main_url + register_path
    # Input data
    data = {
        'phone_number': phone_number
    }
    # Call api
    response = requests.post(api_url, data)
    # Return response data and decode json
    return response.json()


def get_token_from_refresh(refresh_token):
    token = RestRefreshToken(refresh_token)
    return str(token.access_token)


@api_view(['POST', 'GET'])
def logout(request):
    if request.method == 'POST':
        refresh_token = request.data.get('refresh_token', None)
        if refresh_token:
            ref_token = RefreshToken.objects.filter(refresh_token=refresh_token)
            if ref_token.exists():
                current_token = ref_token.first()
                current_token.status = "expired"
                current_token.save()
                token = RestRefreshToken(current_token.refresh_token)
                token.blacklist()
                return Response({'message': 'Logout successful'}, status.HTTP_200_OK)
            return Response({'message': 'Token không tồn tại'}, status.HTTP_400_BAD_REQUEST)
        return Response({'message': 'Bạn cần nhập refresh token'}, status.HTTP_400_BAD_REQUEST)
    else:
        response = {
            'refresh_token': 'token...'
        }
        return Response(response, status=status.HTTP_405_METHOD_NOT_ALLOWED)
