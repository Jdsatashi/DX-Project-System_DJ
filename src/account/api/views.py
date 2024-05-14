import datetime
from functools import partial

import pytz
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, viewsets, status
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken as RestRefreshToken, AccessToken

from account.api.serializers import UserSerializer, RegisterSerializer, response_verify_code, UserUpdateSerializer
from account.handlers.validate_perm import ValidatePermRest
from account.models import User, Verify, PhoneNumber, RefreshToken
from app.api_routes.handlers import get_token_for_user, remove_token_blacklist
from marketing.price_list.models import PriceList, PointOfSeason
from utils.constants import status as user_status, maNhomND
from utils.helpers import generate_digits_code, generate_id, phone_validate
from utils.model_filter_paginate import filter_data


# Register api view
class ApiAccount(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                 mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    authentication_classes = [JWTAuthentication, BasicAuthentication]
    permission_classes = [partial(ValidatePermRest, model=User)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['id', 'username', 'email', 'phone_numbers__phone_number'], *args,
                               **kwargs)
        return Response(response, status.HTTP_200_OK)


class ApiUpdateUserProfile(viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.UpdateModelMixin):
    serializer_class = UserUpdateSerializer
    queryset = User.objects.all()
    # authentication_classes = [JWTAuthentication, BasicAuthentication]
    # permission_classes = [partial(ValidatePermRest, model=User)]


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


@extend_schema(
    methods=['POST'],
    description='Xác thực OTP của user.',
    request={
        'application/json': {
            'example': {
                'otp_code': '123456',
            }
        }
    },
    responses={
        200: "Success",
    }
)
@api_view(['POST'])
def otp_verify(request, pk):
    try:
        phone = PhoneNumber.objects.get(phone_number=pk)
    except PhoneNumber.DoesNotExist:
        return HttpResponse(status=status.HTTP_404_NOT_FOUND)
    if request.method == 'POST':
        # Get verify code from request
        otp_code = request.data.get('otp_code', None)
        # Get verify object from phone number on params
        check_verify = Verify.objects.filter(phone_verify=phone)
        # Check if Phone has assign for verify object
        if not check_verify.exists():
            return Response({'message': 'Số điện thoại không tồn tại trên hệ thống.'}, status=status.HTTP_400_BAD_REQUEST)
        verify = check_verify.latest('created_at')
        # When verify was verified
        if verify.is_verify:
            return Response({'message': 'Tài khoản đã xác thực.'}, status=status.HTTP_400_BAD_REQUEST)
        # When verify code not same with system verify code
        if otp_code != verify.verify_code:
            return Response({'message': 'Mã OTP không chính xác.'}, status=status.HTTP_400_BAD_REQUEST)
        # When verifying success
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
            # Update deactivate other activate token
            if active_token.exists():
                token_obj = active_token.first()
                token_obj.status = "deactivate"
                token_obj.save()
                _token = RestRefreshToken(token_obj.refresh_token)
                _token.blacklist()
            # Create new and save active token
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

    return Response({'message': 'GET method not supported'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


@extend_schema(
    methods=['POST'],
    description='Đăng ký SĐT, nếu SĐT đã tồn tại thì gửi OTP cho user.'
                'Nếu SĐT chưa xác thực sẽ gửi mã OTP cho user.'
                'Nếu SĐT đã xác thực và có refresh_token thì sẽ response access_token mới',
    request={
        'application/json': {
            'example': {
                'phone_number': '0123456789',
                'refresh_token': 'your_access_token_here'
            }
        }
    },
    responses={
        200: "Success",
    }
)
@api_view(['POST'])
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
            response = response_verify_code(new_verify)
            return Response(response, status.HTTP_200_OK)
    return Response({'message': 'GET method not supported'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


@extend_schema(
    methods=['POST'],  # chỉ áp dụng cho POST
    description='Deactivate refresh token của user.',
    request={
        'application/json': {
            'example': {
                'refresh_token': 'your_access_token_here'
            }
        }
    },
    responses={
        200: "Success",
    }
)
@api_view(['POST'])
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
    return Response({'message': 'GET method not supported'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


@extend_schema(
    methods=['POST'],  # chỉ áp dụng cho POST
    description='Xác thực access token và trả về thông tin người dùng.',
    request={
        'application/json': {
            'example': {
                'access_token': 'your_access_token_here'
            }
        }
    },
    responses={
        200: "Success",
    }
)
@api_view(['POST'])
def check_token(request):
    if request.method == 'POST':
        access_token = request.data.get('access_token', None)
        if not access_token:
            return Response({'error': 'No token provided'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = AccessToken(access_token)
            print(f"Decode token: {token['user_id']}")
            user = get_user_model().objects.get(id=token['user_id'])
            print(f"Test exp: {token.check_exp()}")
            current_time = timezone.now()
            expiration_time = datetime.datetime.fromtimestamp(token['exp'], pytz.UTC)
            if current_time < expiration_time:
                today = current_time.date()
                main_pl = PriceList.objects.filter(id='SPTN000015', date_start__lte=today, date_end__gte=today).first()
                point, _ = PointOfSeason.objects.get_or_create(user=user, price_list=main_pl)
                response = UserSerializer(user).data
                response['point'] = point.point
                return Response({'user': response}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Token expired'}, status=status.HTTP_401_UNAUTHORIZED)

        except Exception as e:
            raise e
            # return Response({'error': 'Invalid token', 'details': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
    return Response({'message': 'GET method not supported'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


def call_api_register(phone_number):
    is_valid, phone = phone_validate(phone_number)

    phone = PhoneNumber.objects.filter(phone_number=phone)
    # Get digits number code
    verify_code = generate_digits_code()
    # Case phone Existed but not verify
    if phone.exists():
        phone_num = phone.first()
        verify = Verify.objects.filter(phone_verify=phone_num, is_verify=False)
        # If verified, raise error
        if not verify.exists():
            raise ValidationError({'phone_number': ['Số điện thoại đã xác thực.']})
        verify = verify.first()
        # Update new verify code and time expired
        verify.get_new_code(verify_code)
    else:
        # Handle create user
        type_kh = "client"
        # Generate default id for user client Farmer
        _id = generate_id(maNhomND)
        # Create new user
        user = User.objects.create(id=_id, user_type=type_kh, status=user_status[1], is_active=False)
        # Create new phone number
        phone = PhoneNumber.objects.create(phone_number=phone_number, user=user)
        # Create Verify with data
        verify = Verify.objects.create(user=user, phone_verify=phone, verify_code=verify_code,
                                       verify_type="SMS OTP")

    return response_verify_code(verify)


def get_token_from_refresh(refresh_token):
    token = RestRefreshToken(refresh_token)
    return str(token.access_token)
