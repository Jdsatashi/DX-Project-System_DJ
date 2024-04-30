from django.contrib.auth.hashers import check_password
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenBlacklistView

from account.api.serializers import UserSerializer, PhoneNumberSerializer
from account.models import User, Verify, PhoneNumber
from user_system.user_type.models import UserType
from utils.constants import user_type, status
from utils.helpers import phone_validate


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        username = attrs['username'].upper()
        password = attrs['password']
        is_phone, username = phone_validate(username)
        type_client = UserType.objects.get(user_type=user_type.get('client'))
        if not is_phone:
            print(f"Employee")
            type_emp = UserType.objects.get(user_type=user_type.get('employee'))
            user = User.objects.filter(id=username).first()
        else:
            print(f"Client")
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
        if is_phone:
            verify = Verify.objects.filter(user=user, phone_verify=username).first()
            if not verify.is_verify and user.type == type_client:
                raise AuthenticationFailed('User is not verified!')
            verify.refresh_token = str(token)
            verify.save()

        serializer = UserSerializer(user)
        phone_numbers = user.phone_numbers.all()
        phone_number_serializer = PhoneNumberSerializer(phone_numbers, many=True)
        # Add custom data to token payload
        token['user'] = {
            'user_id': user.id,
            'email': user.email,
            'phone_number': phone_number_serializer.data,
        }
        token['user_id'] = user.id
        response = {
            'refresh': str(token),
            'access': str(token.access_token),
            'user': serializer.data
        }
        if user.user_type == UserType.objects.get(user_type=user_type.get('client')):
            print(username)
            phone = PhoneNumber.objects.get(phone_number=username)
            response['phone_number'] = PhoneNumberSerializer(phone).data
        return response


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


def get_token_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token)
    }


class CustomTokenBlacklistView(TokenBlacklistView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        print("Token has been blacklisted")
        return response
