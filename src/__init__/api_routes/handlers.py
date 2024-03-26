from django.contrib.auth.hashers import check_password
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from account.api.serializers import UserSerializer
from account.models import User


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        usercode = attrs['username'].upper()
        password = attrs['password']

        # Get user object for validating
        user = User.objects.filter(usercode=usercode).first()

        # Validating login request
        if user is None:
            raise AuthenticationFailed(f'User not found!')
        if not check_password(password, user.password):
            raise AuthenticationFailed('Wrong password!')

        # Generate token
        token = super().get_token(user)
        # Add custom data to token payload
        token['user_data'] = {
            'usercode': user.usercode,
            'email': user.email,
            'phone_number': user.phone_number,
            'khuVuc': user.khuVuc,
            'status': user.status,
            'loaiUser': user.loaiUser.loaiUser if user.loaiUser else None,
        }
        token['user_id'] = user.usercode

        return {
            'refresh': str(token),
            'access': str(token.access_token),
        }


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['user_data'] = {
            'usercode': user.usercode,
            'username': user.username,
            'email': user.email,
            'phone_number': user.phone_number,
            'khuVuc': user.khuVuc,
            'status': user.status,
            'loaiUser': user.loaiUser,
        }
        return token


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }
