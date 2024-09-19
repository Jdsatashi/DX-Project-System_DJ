from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError, AuthenticationFailed
from django.http import JsonResponse
from datetime import datetime
from utils.constants import status as user_status
from account.models import TokenMapping


def is_access_token_valid(access_token_jti):
    try:
        # Lấy mapping từ access_token jti
        token_mapping = TokenMapping.objects.get(access_jti=access_token_jti)
        refresh_token_jti = token_mapping.refresh_jti

        # Kiểm tra nếu refresh_token nằm trong OutstandingToken và không bị blacklist
        try:
            outstanding_token = OutstandingToken.objects.get(jti=refresh_token_jti)
            if BlacklistedToken.objects.filter(token=outstanding_token).exists():
                return False
            return True
        except OutstandingToken.DoesNotExist:
            return False
    except TokenMapping.DoesNotExist:
        return False


class CheckBlacklistMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = None
        token = None
        try:
            auth_result = JWTAuthentication().authenticate(request)
            if auth_result is not None:
                user, token = auth_result
        except InvalidToken:
            return JsonResponse({'detail': 'Invalid token', 'code': 'token_not_valid'}, status=401)
        except AuthenticationFailed:
            return JsonResponse({'detail': 'Header token not valid', 'code': 'authentication_failed'}, status=status.HTTP_401_UNAUTHORIZED)

        if user and token:
            try:
                access_token = AccessToken(str(token))
                access_token_jti = access_token['jti']
                if user.status == user_status[1]:
                    return JsonResponse({'detail': 'User is inactive'}, status=401)
                if not is_access_token_valid(access_token_jti):
                    return JsonResponse({'detail': 'Access token\'s related refresh token has been blacklisted',
                                         'code': 'token_not_valid'}, status=401)
            except TokenError as e:
                return JsonResponse({'detail': f'Token error: {e}', 'code': 'token_not_valid'}, status=401)

        response = self.get_response(request)
        return response
