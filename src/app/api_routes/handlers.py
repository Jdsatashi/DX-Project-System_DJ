from django.contrib.auth.hashers import check_password
from rest_framework.exceptions import AuthenticationFailed
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
            'khuVuc': user.khuVuc,
            'status': user.status,
            'loaiUser': user.loaiUser.loaiUser if user.loaiUser else None,
        }
        token['user_id'] = user.id
        return {
            'refresh': str(token),
            'access': str(token.access_token),
        }


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer