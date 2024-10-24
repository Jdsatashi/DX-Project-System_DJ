from datetime import timedelta, datetime

from django.contrib.auth.hashers import check_password
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken as RestRefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenBlacklistView, TokenRefreshView

from account.api.serializers import UserSerializer, PhoneNumberSerializer
from account.models import User, Verify, PhoneNumber, RefreshToken, TokenMapping
from app.logs import app_log
from utils.constants import status
from utils.env import TOKEN_LT
from utils.helpers import phone_validate


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        username = attrs['username'].upper()
        password = attrs['password']
        is_phone, username = phone_validate(username)
        type_client = 'client'
        if not is_phone:
            app_log.info(f"Employee")
            type_emp = 'employee'
            user = User.objects.filter(id=username).first()
        else:
            app_log.info(f"Client")
            user = User.objects.filter(phone_numbers__phone_number__exact=username, user_type=type_client).first()

        # Validating login request
        if user is None:
            raise AuthenticationFailed(f'User not found!')
        if not is_phone and not check_password(password, user.password):
            raise AuthenticationFailed('Wrong password!')
        if user.status == status[1]:
            raise AuthenticationFailed('User is not active!')

        # Generate token
        token = super().get_token(user)
        try:
            refresh_token = token['refresh']
        except KeyError:
            refresh_token = token
        access_token = token.access_token

        # Handle with phone_number
        if is_phone:
            phone = PhoneNumber.objects.get(phone_number=username)
            verify = Verify.objects.filter(user=user, phone_verify=phone).first()
            if not verify.is_verify and user.type == type_client:
                raise AuthenticationFailed('User is not verified!')
            old_token = RefreshToken.objects.filter(user=user, phone_number=phone, status="active")
            if old_token.exists():
                try:
                    deactive_token = old_token.first()
                    # Set token expired
                    deactive_token.status = "expired"
                    deactive_token.save()
                    deactivate_token = RestRefreshToken(deactive_token.refresh_token)
                    deactivate_token.blacklist()
                except TokenError:
                    app_log.info("Token error")
            access_token['phone_number'] = phone.phone_number
            token_save = RefreshToken.objects.create(user=user, phone_number=phone, refresh_token=str(refresh_token), status="active")

        serializer = UserSerializer(user)
        # Add custom data to token payload

        TokenMapping.objects.create(
            user=user,
            refresh_jti=token['jti'],  # JTI of refresh token
            access_jti=access_token['jti'],  # JTI of access token
            expired_at=datetime.now() + timedelta(hours=int(TOKEN_LT))  # Thời gian hết hạn của access token
        )
        response = {
            'refresh': str(refresh_token),
            'access': str(access_token),
            'user': serializer.data
        }
        if user.user_type == 'client':
            phone = PhoneNumber.objects.get(phone_number=username)
            response['phone_number'] = PhoneNumberSerializer(phone).data
        return response


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        refresh = attrs['refresh']
        refresh_token = RestRefreshToken(str(refresh))

        data = super().validate(attrs)
        access_token = refresh_token.access_token

        # Lưu jti của tokens vào bảng TokenMapping
        TokenMapping.objects.create(
            user=User.objects.get(id=refresh_token['user_id']),
            refresh_jti=refresh_token['jti'],
            access_jti=access_token['jti'],
            expired_at=datetime.now() + timedelta(hours=int(TOKEN_LT))  # Thời gian hết hạn của access token
        )

        data['access'] = str(access_token)
        return data


class CustomTokenRefreshView(TokenRefreshView):
    serializer_class = CustomTokenRefreshSerializer


class ContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        fields = '__all__'


class ApiContentType(APIView):
    def get(self, request):
        content_list = ContentType.objects.all()
        serializer = ContentTypeSerializer(content_list, many=True)
        return Response(serializer.data)


def get_token_for_user(user):
    refresh = RestRefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token)
    }


class CustomTokenBlacklistView(TokenBlacklistView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        app_log.info("Token has been blacklisted")
        return response


def remove_token_blacklist(token: str):
    _token = OutstandingToken.objects.filter(token=token).first()
    BlacklistedToken.objects.filter(token=_token).delete()
