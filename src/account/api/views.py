import datetime
import time

import pytz
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.db.models import Q, Max
from django.http import HttpResponse
from django.shortcuts import render
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, viewsets, status
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken as RestRefreshToken, AccessToken

from account.api.serializers import UserSerializer, RegisterSerializer, response_verify_code, UserUpdateSerializer, \
    UserWithPerm, PermSerializer, GroupPermSerializer, UserListSerializer, AllowanceOrder
from account.handlers.perms import get_perm_name
from account.models import User, Verify, PhoneNumber, RefreshToken, TokenMapping, GroupPerm, Perm
from account.queries import get_all_user_perms_sql
from app.api_routes.handlers import get_token_for_user
from app.logs import app_log
from app.settings import pusher_client
from marketing.order.models import Order
from marketing.price_list.models import PriceList, PointOfSeason, SpecialOffer
from user_system.client_profile.api.serializers import ClientProfileSerializer
from user_system.client_profile.models import ClientProfile
from user_system.employee_profile.api.serializers import EmployeeProfileSerializer
from utils.constants import status as user_status, maNhomND, admin_role, phone_magic, magic_verify_code
from utils.env import TOKEN_LT
from utils.helpers import generate_digits_code, generate_id, phone_validate, local_time, check_email
from utils.insert_db.default_roles_perms import set_user_perm
from utils.model_filter_paginate import filter_data


# Register api view
class ApiAccount(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                 mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = UserWithPerm
    queryset = User.objects.all()

    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]

    # permission_classes = [partial(ValidatePermRest, model=User)]

    def list(self, request, *args, **kwargs):
        start_time = time.time()
        queryset = self.get_queryset()

        self.serializer_class = UserListSerializer

        get_user = self.request.query_params.get('get_user', None)
        match get_user:
            case 'nvtt':
                app_log.info(f"Case nvtt")
                queryset = User.objects.filter(
                    group_user__name='nvtt'
                )
            case 'client':
                app_log.info(f"Case client")
                queryset = queryset.filter(user_type='client')
            case 'employee':
                app_log.info(f"Case employee")
                queryset = queryset.filter(user_type='employee').exclude(group_user__name='admin')
            case 'farmer':
                app_log.info(f"Case farmer")
                queryset = queryset.filter(user_type='farmer')
            case 'admin':
                app_log.info(f"Case admin")
                # queryset = queryset.filter(is_superuser=True)
                queryset = queryset.filter(group_user__name='admin')
            case 'npp':
                app_log.info(f"Case npp")
                queryset = queryset.filter(Q(clientprofile__is_npp=True) | Q(group_user__name='npp'))
            case 'daily':
                app_log.info(f"Case daily")
                queryset = queryset.filter(user_type='client').exclude(
                    Q(group_user__name='npp') | Q(clientprofile__is_npp=True))
            case _:
                app_log.info(f"Case default")
                pass
        queryset = queryset.distinct()
        response = filter_data(self, request, ['id', 'username', 'email', 'phone_numbers__phone_number',
                                               'clientprofile__register_name', 'employeeprofile__register_name'],
                               queryset=queryset, **kwargs)
        app_log.info(f"Query time: {time.time() - start_time}")
        return Response(response, status.HTTP_200_OK)


class ApiUpdateUserProfile(viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.UpdateModelMixin):
    serializer_class = UserUpdateSerializer
    queryset = User.objects.all()
    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]
    # permission_classes = [partial(ValidatePermRest, model=User)]


class RegisterSMS(APIView):
    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]

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
            return Response({'message': 'Số điện thoại không tồn tại trên hệ thống.'},
                            status=status.HTTP_400_BAD_REQUEST)
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
            verify.verify_time = local_time()
            # Activate user
            verify.user.status = user_status[0]
            verify.user.is_active = True
            verify.user.save()
            verify.save()
            # Generate new token
            token = get_token_for_user(verify.user)
            set_user_perm(verify.user, True)
            # Add data for refresh token
            deactivate_user_token(verify.user)
            try:
                refresh_token = token['refresh']
            except TokenError:
                app_log.info(TokenError)
                refresh_token = token
            app_log.info(f"Test refresh token: {str(refresh_token)}")
            access_token = create_access_token_from_refresh(str(refresh_token), pk)
            # Create new and save active token
            ref_token = RefreshToken.objects.create(user=verify.user, phone_number=phone,
                                                    refresh_token=str(refresh_token), status="active")
            verify.refresh_token = ref_token
            verify.save()
            # Add response data
            serializer = UserSerializer(verify.user)
            pusher_login(verify.user)
            response = {'message': 'Successful verify phone number', 'user': serializer.data, 'phone_number': pk,
                        'token': {
                            'refresh': str(refresh_token),
                            'access': str(access_token)
                        }}
            return Response(response, status=status.HTTP_200_OK)
        app_log.info("OTP code is expired")
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
def phone_login_2(request):
    if request.method == 'POST':
        phone_number = request.data.get('phone_number', None)
        refresh_token = request.data.get('refresh_token', None)
        if phone_number is None:
            return Response({'message': 'Bạn cần nhập số điện thoại'}, status=status.HTTP_400_BAD_REQUEST)
        app_log.debug(f"Check token: {refresh_token}")
        # Trying get Phone if exist
        try:
            phone = PhoneNumber.objects.get(phone_number=phone_number)
        # When not exist, register this phone number
        except PhoneNumber.DoesNotExist:
            response_data = create_verify_user(phone_number)
            return Response(response_data)
        # Get user from phone object
        user = phone.user
        app_log.info(f"Test token: {refresh_token}")
        if refresh_token:
            # Get new token
            try:
                new_token = create_access_token_from_refresh(refresh_token, phone_number)
            except TokenError:
                # If get new token error, refresh_token error
                return Response({'message': 'Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại'},
                                status=status.HTTP_401_UNAUTHORIZED)
            pusher_login(user)
            # Return token when not error
            return Response({'refresh': refresh_token, 'access': new_token}, status.HTTP_200_OK)
        else:
            verify_code = generate_digits_code()
            if phone_number == phone_magic:
                verify_code = magic_verify_code
            new_verify = Verify.objects.create(user=user, phone_verify=phone, verify_code=verify_code,
                                               verify_type="SMS OTP")
            response = response_verify_code(new_verify)
            return Response(response, status.HTTP_200_OK)
    return Response({'message': 'method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


@extend_schema(
    methods=['POST'],  # chỉ áp dụng cho POST
    description='Login user admin',
    request={
        'application/json': {
            'example': {
                'email': 'adminaccount',
                'password': '123456'
            }
        }
    },
    responses={
        200: "Success",
    }
)
@api_view(['POST'])
def admin_login(request):
    if request.method == 'POST':
        # username = request.data.get('username', None)
        email = request.data.get('email', '')
        password = request.data.get('password', None)

        if not check_email(email):
            return Response({'message': 'invalid email'}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.filter(email=email).first()
        # Validating user
        if user is None:
            return Response({'message': 'email is not found in system'}, status=status.HTTP_400_BAD_REQUEST)
        if not check_password(password, user.password):
            return Response({'message': 'wrong password'}, status=status.HTTP_400_BAD_REQUEST)
        # Check if user is admin
        app_log.info(f"Test role exist: {user.group_user.filter(name=admin_role).exists()}")
        if not user.is_superuser and not user.group_user.filter(name=admin_role).exists():
            return Response({'message': 'user not allow to access this page'}, status=status.HTTP_406_NOT_ACCEPTABLE)
        # Generate new token for user
        refresh = RestRefreshToken.for_user(user)
        access_token = refresh.access_token
        # Get active token
        deactivate_user_token(user)
        # Save current token
        RefreshToken.objects.create(user=user, refresh_token=str(refresh), status="active")
        # Create TokenMapping for verifying
        TokenMapping.objects.create(
            user=user,
            access_jti=access_token['jti'],
            refresh_jti=refresh['jti']
        )
        pusher_login(user)
        return Response({'refresh': str(refresh), 'access': str(access_token)}, status=status.HTTP_200_OK)

    return Response({'message': 'method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


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
        # Get authentication headers
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            # Get access token from headers
            access_token = auth_header.split(' ')[1]
        else:
            return Response({"error": "Access token not provided"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            # Decode access token
            token = AccessToken(str(access_token))
            # Get user object from user id in access token
            user = get_user_model().objects.get(id=token['user_id'])
            app_log.info(f"Access token of user {user.id}")
            # Get time to verify lifetime
            current_time = local_time()
            expiration_time = datetime.datetime.fromtimestamp(token['exp'], pytz.UTC)
            # When in lifetime
            if current_time < expiration_time:
                response_data = dict()
                # Check user is admin
                user_data = UserSerializer(user).data
                if not user.is_superuser and not user.group_user.filter(name=admin_role).exists():
                    # If not admin calculate point
                    main_pl = PriceList.get_main_pl()
                    point, _ = PointOfSeason.objects.get_or_create(user=user, price_list=main_pl)
                    # Create json response data of user
                    user_data['point'] = point.point
                else:
                    response_data['is_admin'] = True
                # Get profile user depend on user_type
                if user.user_type == 'employee':
                    profile = EmployeeProfileSerializer(user.employeeprofile).data
                else:
                    profile = ClientProfileSerializer(user.clientprofile).data
                # Add profile to user_data
                user_data['profile'] = profile
                # Get all group of user
                group = user.group_user.filter().values_list('name', flat=True)
                # Add group to user_data
                user_data['group'] = list(group)
                # Add user data to response data
                response_data['user'] = user_data
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Token expired'}, status=status.HTTP_401_UNAUTHORIZED)

        except Exception as e:
            # raise e
            return Response({'error': 'Invalid token or Token was expired', 'details': str(e)},
                            status=status.HTTP_401_UNAUTHORIZED)
    return Response({'message': 'GET method not supported'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


def create_verify_user(phone_number):
    is_valid, phone = phone_validate(phone_number)

    verify_code = generate_digits_code()

    if phone_number == phone_magic:
        verify_code = magic_verify_code

    phone = PhoneNumber.objects.filter(phone_number=phone)
    # Get digits number code
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
        type_kh = 'farmer'
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


def create_access_token_from_refresh(refresh_token_str, phone_number):
    refresh_token = RestRefreshToken(refresh_token_str)
    access_token = refresh_token.access_token
    access_token['phone_number'] = phone_number

    user = User.objects.get(id=refresh_token['user_id'])
    TokenMapping.objects.create(
        user=user,
        access_jti=access_token['jti'],
        refresh_jti=refresh_token['jti'],
        expired_at=local_time() + datetime.timedelta(hours=int(TOKEN_LT))
    )

    return str(access_token)


def pusher_login(user):
    channel = f"user_{user.id}"
    event = f"login"
    login_at = local_time()
    data = {'chanel': channel, 'event': event, 'login_at': str(login_at)}
    try:
        app_log.info(f"Input pusher: {data}")
        pusher_client.trigger(channel, event, {'login_time': str(login_at)})
    except Exception as e:
        app_log.info(e)
        raise e


def deactivate_user_token(user):
    token_obj = RefreshToken.objects.filter(user=user, status="active").first()
    # Update deactivate other activate token
    if token_obj:
        token_obj.status = "expired"
        token_obj.save()
        _token = RestRefreshToken(token_obj.refresh_token)
        _token.blacklist()


class ApiGroupPerm(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = GroupPermSerializer
    queryset = GroupPerm.objects.all()
    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]

    # permission_classes = [partial(ValidatePermRest, model=User)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['name'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)


class ApiPerm(viewsets.GenericViewSet, mixins.ListModelMixin,
              mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = PermSerializer
    queryset = Perm.objects.all()
    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]

    # permission_classes = [partial(ValidatePermRest, model=User)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['name'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)


class ApiUpdateDeviceCode(APIView):
    def post(self, request):
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            # Get access token from headers
            access_token = auth_header.split(' ')[1]
        else:
            return Response({"error": "Access token not provided"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            # Decode access token
            token = AccessToken(str(access_token))
            # Get user object from user id in access token
            user = get_user_model().objects.get(id=token['user_id'])
            device_code = request.data.get('device_code', None)
            user.device_token = device_code
            user.save()
            return Response({'user_id': user.id, 'device_token': user.device_token}, status=status.HTTP_200_OK)
        except Exception as e:
            # raise e
            return Response({'error': 'Invalid token or Token was expired', 'details': str(e)},
                            status=status.HTTP_401_UNAUTHORIZED)
        # user_id = request.data.get('user_id', None)
        # device_code = request.data.get('device_code', None)
        # try:
        #     user = User.objects.filter(id=user_id).first()
        #     if not user:
        #         return Response({'message': f'error not found user with id \'{user_id}\''})
        #     user.device_token = device_code
        #     user.save()
        # except Exception as e:
        #     app_log.error(f'Get error ApiUpdateDeviceCode post')
        #     raise e
        # return Response({'message': 'Success'}, status=status.HTTP_200_OK)


class ApiGetManageUser(APIView):
    # authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]

    def get(self, request):
        # Get user for checking manage group user
        user = request.user
        if not request.user.is_authenticated:
            ctx = {'message': "Bạn chưa đăng nhập."}
            return render(request, 'errors/403.html', ctx)
        user_id = request.query_params.get('user', '')
        if user_id != '':
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({'error': 'user id in query params not found'}, status=status.HTTP_400_BAD_REQUEST)

        # Check type of user
        user_type = check_user_type(user)
        highest_group = get_highest_level_group(user)

        if user_type == 'nvtt':
            users_list = User.objects.filter(clientprofile__nvtt_id=user.id)
            get_user = request.query_params.get('get_user', '')
            if get_user == 'npp':
                users_list = users_list.filter(Q(clientprofile__is_npp=True) | Q(group_user__name='npp'))
            elif get_user == 'daily':
                users_list = users_list.exclude(Q(clientprofile__is_npp=True) | Q(group_user__name='npp'))
            user_name = user.employeeprofile.register_name
        elif user_type == 'npp':
            users_list = User.objects.filter(clientprofile__client_lv1_id=user.id)
            user_name = user.clientprofile.register_name
        else:
            return Response({'data': []}, status=status.HTTP_200_OK)

        query = request.query_params.get('query', '')
        if query != '':
            users_list = search_users(query, users_list)

        user_data = format_user_data(users_list)

        response_data = {
            'user_id': user.id,
            'name': user_name,
            'group_manage': user_data
        }

        return Response(response_data, status=status.HTTP_200_OK)

    def post(self, request):
        user = request.user
        if not request.user.is_authenticated:
            ctx = {'message': "Bạn chưa đăng nhập."}
            return render(request, 'errors/403.html', ctx)
        serializer = AllowanceOrder(data=request.data)
        if serializer.is_valid():
            manage_user = serializer.validated_data['manage_user']
            entrust_users = serializer.validated_data['entrust_user']
            try:
                manage_user_obj = User.objects.get(id=manage_user)
            except User.DoesNotExist:
                return Response({'error': f'not found user {manage_user}'}, status=status.HTTP_400_BAD_REQUEST)

            app_log.info(f"Manage user: {manage_user}")
            app_log.info(f"Entrust user: {entrust_users}")
            user_type = check_user_type(manage_user_obj)
            print(f"Test user type: {user_type}")
            # order_perm = get_perm_name(Order)
            # pl_perm = get_perm_name(PriceList)
            # so_perm = get_perm_name(SpecialOffer)
            before_manage_perm = list(manage_user_obj.perm_user.filter().distinct())

            if user_type == 'nvtt':
                # user_obj = User.objects.get(id=entrust_users.get('user_id'))
                user_perms = get_all_user_perms_sql(entrust_users.get('user_id'))

            elif user_type == 'npp':
                pass
            else:
                return Response({'error': f'user {manage_user} is not manager (nvtt, npp)'}, status=status.HTTP_200_OK)
            print(before_manage_perm)
            return Response({'message': 'ok'}, 200)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def search_users(query, users_list):
    search_queries = query.split(',')
    search_fields = ['id', 'username', 'email', 'phone_numbers__phone_number', 'clientprofile__register_name']
    q_objects = Q()
    for search in search_queries:
        for field in search_fields:
            q_objects |= Q(**{f"{field}__icontains": search})
    return users_list.filter(q_objects)


def format_user_data(users_list):
    user_data = []
    user_type = 'daily'
    for user in users_list:
        user_name_ = user.clientprofile.register_name or ''
        if user.clientprofile.is_npp or user.group_user.filter(name='npp').exists():
            user_type = 'npp'
        user_phones = user.phone_numbers.filter().values_list('phone_number', flat=True)
        user_dict = {
            'id': user.id,
            'name': user_name_,
            'phone': list(user_phones),
            'user_type': user_type
        }
        user_data.append(user_dict)
    return user_data


def get_client_npp(npp_id):
    clients = User.objects.filter(Q(clientprofile__client_lv1_id=npp_id))
    return clients


def get_highest_level_group(user):
    max_level = user.group_user.aggregate(Max('level'))['level__max']
    app_log.info(f"Level: {max_level}")

    highest_level_group = user.group_user.filter(level=max_level).first()

    return highest_level_group.name


def check_user_type(user):
    if user.user_type == 'employee' and user.group_user.filter(name='admin').exists():
        return 'admin'
    if user.group_user.filter(name='nvtt').exists():
        return 'nvtt'
    if user.user_type == 'employee' and not user.group_user.filter(name='admin').exists():
        return 'employee'
    if user.user_type == 'client' and user.clientprofile.is_npp:
        return 'npp'
    if user.user_type == 'client' and not user.clientprofile.is_npp:
        return 'daily'
    if user.user_type == 'farmer':
        return 'farmer'
    return 'unknown'
