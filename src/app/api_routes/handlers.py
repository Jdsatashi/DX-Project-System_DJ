from django.contrib.auth.hashers import check_password
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from account.models import User


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        user_id = attrs['username'].upper()
        password = attrs['password']

        # Get user object for validating
        user = User.objects.filter(id=user_id).first()

        # Validating login request
        if user is None:
            raise AuthenticationFailed(f'User not found!')
        if not check_password(password, user.password):
            raise AuthenticationFailed('Wrong password!')
        # Generate token
        token = super().get_token(user)

        # Add custom data to token payload
        token['user'] = {
            'user_id': user.id,
            'email': user.email,
            'phone_number': user.phone_number,
            'region': user.region,
            'status': user.status,
            'loaiUser': user.user_type.user_type if user.user_type else None,
        }
        token['user_id'] = user.id
        return {
            'refresh': str(token),
            'access': str(token.access_token),
        }


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class ContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        fields = '__all__'


class ApiContentType(APIView):
    def get(self, request):
        content_list = ContentType.objects.all()
        serializer = ContentTypeSerializer(content_list, many=True)
        return Response(serializer.data)
