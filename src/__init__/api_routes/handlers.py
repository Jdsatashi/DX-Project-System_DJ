from django.contrib.auth.hashers import check_password
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from account.api.serializers import UserSerializer
from account.models import User


class CustomTokenObtainPairSerializer(serializers.Serializer):
    usercode = serializers.CharField(max_length=64)
    password = serializers.CharField(max_length=255)

    def validate(self, attrs):
        usercode = attrs['usercode'].upper()
        password = attrs['password']

        # Get user object for validating
        user = User.objects.filter(usercode=usercode).first()
        user.id = user.usercode
        # Validating login request
        if user is None:
            raise AuthenticationFailed(f'User not found!')
        if not check_password(password, user.password):
            return Response({'message': 'Wrong password!'})
        user_data = UserSerializer(user).data
        tokens = get_tokens_for_user(user)
        tokens['users'] = user_data
        return tokens


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }
