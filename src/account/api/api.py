import datetime
import jwt
import os
import time

from django.contrib.auth.hashers import check_password
from django.http import HttpResponse, JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from account.api.serializers import UserSerializer
from account.handle import handle_create_acc, handle_list_acc
from account.models import User, LoginToken


def api_create_user(req):
    ctx = handle_create_acc(req)
    return HttpResponse(ctx, content_type='application/json')


def api_list_user(request):
    start = time.time()
    token = request.COOKIES.get('token')
    ctx = {}
    if not token:
        ctx['message'] = 'Unauthorized'
        return JsonResponse(ctx)
    ctx['token'] = token
    ctx = handle_list_acc(request)
    ctx = list(ctx['users'].values())
    for user in ctx:
        user.pop('last_login')
        user.pop('is_superuser')
    print(time.time() - start)
    return JsonResponse(ctx)


# Register api view
class ApiRegister(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# Login api view
class ApiLogin(APIView):
    def post(self, request):
        # Get request data
        user_id = request.data.get('user_id')
        user_id = user_id.upper()
        password = request.data.get('password')
        # Get user object for validating
        user = User.objects.filter(id=user_id).first()
        # Validating login request
        if user is None:
            return Response({'message': 'User not found'}, status.HTTP_401_UNAUTHORIZED)
        if not check_password(password, user.password):
            return Response({'message': 'Wrong password!'}, status=status.HTTP_401_UNAUTHORIZED)
        # Set data for create jwt token
        expired = datetime.datetime.utcnow() + datetime.timedelta(minutes=60)
        payload = {
            'id': user_id,
            'exp': expired,
            'iat': datetime.datetime.utcnow()
        }
        # Create token
        token = jwt.encode(payload, os.environ.get('SECRET_KEY'), algorithm='HS256').decode('utf-8')
        # Save token to datababse
        login_data = LoginToken.objects.create(user=user, token=token, status='active', expired_at=expired)
        # Create response
        response = Response()
        response.set_cookie(key='jwt', value=token, httponly=True)
        response.data = {
            'message': f'Login success! Welcome {user.id}',
            'data': {
                'user': UserSerializer(user).data,
                'login_data': {
                    'token': login_data.token,
                    'expired_at': login_data.expired_at,
                }
            }
        }
        response.status_code = status.HTTP_200_OK
        return response


# Logout api
class ApiLogout(APIView):
    def post(self, request):
        user_id = request.data.get('user_id')
        token = request.COOKIES.get('jwt')
        user = User.objects.filter(id=user_id.upper()).first()
        if not user:
            return Response({'message': 'User not found'}, status=status.HTTP_401_UNAUTHORIZED)
        LoginToken.objects.get(user=user, token=token).delete()
        response = Response()
        response.delete_cookie('jwt')
        response.data = {'message': 'Logged out successfully'}
        return response


# Checking token function
def verify_token(token):
    try:
        payload = jwt.decode(token, os.environ.get('SECRET_KEY'), algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return {
            'valid': False,
            'message': 'Unauthenticated'
        }
    return {
        'valid': True,
        'data': payload
    }


# Test token
class ApiTest(APIView):
    def get(self, request):
        token = request.COOKIES.get('jwt')
        if not token:
            return Response({'message': 'unauthorized'})
        verify = verify_token(token)
        user_id = verify.get('data').get('id')
        if not verify:
            return Response({'message': verify.get('message')})
        user = User.objects.get(id=user_id)
        serializer = UserSerializer(user)
        return Response({'data': serializer.data})


# Get public ip of client
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
