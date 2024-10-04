import traceback

import requests
from django.contrib.auth.hashers import make_password
from django.db import transaction, IntegrityError
from django.db.models import Q
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from account.handlers.token import deactivate_user_token, deactivate_user_phone_token
from account.models import User, GroupPerm, Perm, Verify, PhoneNumber, GrantAccess
from app.logs import app_log
from app.settings import SMS_SERVICE
from user_system.client_profile.api.serializers import ClientProfileUserSerializer, ClientGroupView
from user_system.client_profile.models import ClientProfile, ClientGroup
from user_system.employee_profile.api.serializers import EmployeeProfileUserSerializer
from user_system.employee_profile.models import EmployeeProfile
from utils.constants import maNhomND, status
from utils.helpers import phone_validate, generate_id, generate_digits_code
from datetime import timedelta, datetime


class PhoneNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhoneNumber
        fields = ['phone_number']


# Create user serializer for rest api form
class UserSerializer(serializers.ModelSerializer):
    # Field meta
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'region', 'status', 'user_type']
        extra_kwargs = {
            'username': {'required': False},
            'email': {'required': False},
            'password': {'write_only': True}
        }


class ClientProfileList(serializers.ModelSerializer):
    client_group = ClientGroupView(source='client_group_id', read_only=True)
    nvtt = serializers.SerializerMethodField()
    client_lv1 = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ClientProfile
        fields = ['register_name', 'address', 'client_group', 'is_npp', 'client_lv1', 'nvtt']

    def get_nvtt(self, obj):
        nvtt_id = obj.nvtt_id
        nvtt = User.objects.filter(id=nvtt_id).select_related('employeeprofile').first()
        if nvtt is None:
            return None
        return {
            'id': nvtt_id,
            'name': nvtt.employeeprofile.register_name
        }

    def get_client_lv1(self, obj):
        client_lv1_id = obj.client_lv1_id
        client_lv1 = ClientProfile.objects.filter(client_id_id=client_lv1_id).first()
        if client_lv1 is None:
            return None
        return {
            'id': client_lv1_id,
            'name': client_lv1.register_name
        }


class EmployeeProfileList(serializers.ModelSerializer):
    class Meta:
        model = EmployeeProfile
        fields = ['register_name', 'address', 'department', 'position']


class GroupNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupPerm
        fields = ['name', 'display_name']


class UserListSerializer(serializers.ModelSerializer):
    phone = serializers.SerializerMethodField()
    profile = serializers.SerializerMethodField()
    main_phone = serializers.SerializerMethodField()
    group_user = GroupNameSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'status', 'note', 'user_type', 'phone', 'main_phone', 'group_user', 'profile']

    def get_phone(self, obj):
        return list(obj.phone_numbers.values_list('phone_number', flat=True))

    def get_profile(self, obj):
        if obj.user_type in ['client', 'farmer']:
            client_profile = getattr(obj, 'clientprofile', None)
            return ClientProfileList(client_profile).data if client_profile else None
        elif obj.user_type == 'employee':
            employee_profile = getattr(obj, 'employeeprofile', None)
            return EmployeeProfileList(employee_profile).data if employee_profile else None
        return None

    def get_main_phone(self, obj):
        main_phone = obj.phone_numbers.filter(type='main').first()
        if main_phone:
            print(f"{main_phone.phone_number}")
            return main_phone.phone_number
        return None


class ClientInfo(serializers.ModelSerializer):
    class Meta:
        model = ClientProfile
        fields = ['register_name', 'organization', 'dob', 'address']


class EmployeeInfo(serializers.ModelSerializer):
    class Meta:
        model = EmployeeProfile
        fields = ['register_name', 'gender', 'dob', 'address']


class UserUpdateSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'note', 'region', 'user_type', 'profile']
        read_only_fields = ['id', 'username', 'user_type']

    @staticmethod
    def get_profile(obj):
        if obj.user_type == 'client':
            client_profile = ClientProfile.objects.get(client_id=obj)
            return ClientInfo(client_profile).data
        elif obj.user_type == 'employee':
            employee_profile = EmployeeProfile.objects.get(employee_id=obj)
            return EmployeeInfo(employee_profile).data
        return None


class RegisterSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(max_length=24, allow_null=False)

    class Meta:
        model = User
        fields = ['id', 'status', 'user_type', 'phone_number']
        read_only_fields = ['id', 'status', 'user_type']

    def create(self, validated_data):
        phone_number = validated_data.pop('phone_number')
        if phone_number is None or phone_number == '':
            raise serializers.ValidationError({'phone_number': ['Bạn phải nhập số điện thoại.']})
        # Handle here
        is_valid, phone = phone_validate(phone_number)
        if not is_valid:
            raise serializers.ValidationError({'phone_number': ['Số điện thoại không hợp lệ.']})
        # Get object phone number
        phone = PhoneNumber.objects.filter(phone_number=phone)
        # Get digits number code
        verify_code = generate_digits_code()
        # Case phone Existed but not verify
        if phone.exists():
            phone_num = phone.first()
            verify = Verify.objects.filter(phone_verify=phone_num, is_verify=False)
            # If verified, raise error
            if not verify.exists():
                raise serializers.ValidationError({'message': ['Số điện thoại đã xác thực.']})
            verify = verify.first()
            # Update new verify code and time expired
            verify.get_new_code(verify_code)
        else:
            # Handle create user
            type_kh = "client"
            # Generate default id for user client Farmer
            _id = generate_id(maNhomND)
            # Create new user
            user = User.objects.create(id=_id, user_type=type_kh, status=status[1], is_active=False)
            # Create new phone number
            phone = PhoneNumber.objects.create(phone_number=phone_number, user=user)
            client_group = ClientGroup.objects.get(id=maNhomND)
            # Create new default Profile for user as type Client
            ClientProfile.objects.create(client_id=user, client_group_id=client_group)
            # Create Verify with data
            verify = Verify.objects.create(user=user, phone_verify=phone, verify_code=verify_code,
                                           verify_type="SMS OTP")
        message = f"[DONG XANH] Ma xac thuc cua ban la {verify.verify_code}, tai app Thuoc BVTV Dong Xanh co "
        f"hieu luc trong 3 phut. Vi ly do bao mat tuyet doi khong cung cap cho bat ky ai."
        send_sms(phone_number, message)

        return response_verify_code(verify)


class GroupPermSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupPerm
        exclude = ['perm']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        perms = instance.perm.all()
        request = self.context.get('request')
        if (request and request.method == 'GET'
                and hasattr(request, 'resolver_match')
                and request.resolver_match.kwargs.get('pk')):
            perms = [perm.name for perm in perms]
            representation['perm'] = perms
        else:
            perms = [perm.name for perm in perms[:5]]
            representation['perm'] = perms + ['...'] if len(perms) >= 5 else perms
        return representation


class PermSerializer(serializers.ModelSerializer):
    class Meta:
        model = Perm
        fields = '__all__'
        read_only_fields = ['name', 'created_at', 'updated_at', 'content_type', 'object_id']


class UserWithPerm(serializers.ModelSerializer):
    group = serializers.ListField(child=serializers.CharField(), write_only=True, required=False, allow_null=True)
    perm = serializers.ListField(child=serializers.CharField(), write_only=True, required=False, allow_null=True)
    phone = serializers.ListField(child=serializers.CharField(), write_only=True, required=False, allow_null=True)
    profile = serializers.JSONField(write_only=True, required=False, allow_null=True)
    group_user = GroupNameSerializer(many=True, read_only=True)
    main_phone = serializers.CharField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = User
        # fields = '__all__'
        exclude = ['is_staff', 'is_superuser', 'last_login', 'groups', 'user_permissions']
        extra_kwargs = {
            'id': {'required': False},
            'username': {'required': False},
            'email': {'required': False},
            'password': {'required': False, 'write_only': True}
        }

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['phone'] = [phone.phone_number for phone in instance.phone_numbers.all()]
        main_phone = instance.phone_numbers.filter(type='main').first()
        if main_phone:
            print(f"{main_phone.phone_number}")
            representation['main_phone'] = main_phone.phone_number
        else:
            representation['main_phone'] = None
        # Add profile data to representation
        if instance.user_type == 'employee':
            profile = EmployeeProfile.objects.filter(employee_id=instance).first()
            if profile:
                representation['profile'] = EmployeeProfileUserSerializer(profile).data
        else:
            profile = ClientProfile.objects.filter(client_id=instance).first()
            print(f"HERE TEST: {profile}")
            if profile:
                representation['profile'] = ClientProfileUserSerializer(profile).data
        # Add perm_user data to representation
        perm_user = [perm.name for perm in instance.perm_user.all()]

        request = self.context.get('request')
        if (request and request.method == 'GET'
                and hasattr(request, 'resolver_match')
                and request.resolver_match.kwargs.get('pk')):
            representation['perm_user'] = perm_user
        else:
            perm_user = perm_user[:5]
            representation['perm_user'] = perm_user + ['...'] if len(perm_user) >= 5 else perm_user

        return representation

    def create(self, validated_data):
        group_data = validated_data.pop('group', None)
        perm_data = validated_data.pop('perm', None)
        phone_data = validated_data.pop('phone', None)
        profile_data = validated_data.pop('profile', None)
        main_phone = validated_data.pop('main_phone', None)

        try:
            with transaction.atomic():
                email = validated_data.get('email')
                app_log.info(f"Email: {email}")
                app_log.info(f"{email and email != '' and User.objects.filter(email=email).exists()}")
                if email and email != '' and User.objects.filter(email=email).exists():
                    raise serializers.ValidationError(
                        {'message': f"email '{email}' already exists"})
                if validated_data.get('password', None):
                    validated_data['password'] = make_password(validated_data['password'])
                user = User.objects.create(**validated_data)
                print(f"Test main phone: {main_phone}")
                # Create phone
                if phone_data:
                    for phone_number in phone_data:
                        # Validate phone number
                        is_valid, phone_number = phone_validate(phone_number)
                        if not is_valid:
                            raise serializers.ValidationError({'message': f'"{phone_number}" không hợp lệ'})
                        try:
                            phone = PhoneNumber.objects.create(phone_number=phone_number, user=user)
                            if phone.phone_number == main_phone:
                                phone.type = 'main'
                                phone.save()
                        except IntegrityError:
                            raise serializers.ValidationError(
                                {'message': f'"{phone_number}" đã tồn tại'})
                handle_user(user, group_data, perm_data, profile_data)
        except serializers.ValidationError as ve:
            raise ve
        except Exception as e:
            # Log the exception if needed
            error_message = traceback.format_exc()
            app_log.error(f"Error creating user: \n{e}\n--- Details: {error_message}")
            # Rollback transaction and re-raise the exception
            raise ValidationError({'message': 'unexpected error when create user'})

        return user

    def update(self, instance, validated_data):
        group_data = validated_data.pop('group', None)
        perm_data = validated_data.pop('perm', None)
        phone_data = validated_data.pop('phone', None)
        profile_data = validated_data.pop('profile', None)
        main_phone = validated_data.pop('main_phone', None)

        try:
            with transaction.atomic():
                # Update user fields
                for attr, value in validated_data.items():
                    if attr == 'password':
                        value = make_password(value)
                    setattr(instance, attr, value)
                instance.save()

                # Update phone
                if phone_data is not None:
                    current_phone = instance.phone_numbers.filter().values_list('phone_number', flat=True).distinct()
                    add_phone = set(phone_data) - set(list(current_phone))
                    remove_phone = list(set(list(current_phone)) - set(phone_data))

                    # Loop inserting data phone
                    for phone_number in add_phone:
                        is_valid, phone_number = phone_validate(phone_number)
                        if not is_valid:
                            raise serializers.ValidationError({'message': f'\'{phone_number}\' không hợp lệ'})
                        try:
                            PhoneNumber.objects.create(phone_number=phone_number, user=instance)
                        except IntegrityError:
                            raise serializers.ValidationError(
                                {'message': f'phone_number \'{phone_number}\' đã tồn tại'})
                    if len(remove_phone) >= 1:
                        # deactivate_user_token(instance)
                        for phone_number in remove_phone:
                            phone = PhoneNumber.objects.get(phone_number=phone_number)
                            deactivate_user_phone_token(instance, phone)
                            phone.delete()
                    if main_phone:

                        main_phone_obj = instance.phone_numbers.filter(phone_number=main_phone)
                        if main_phone_obj.exists():
                            origin_main = instance.phone_numbers.filter(type='main').first()
                            if origin_main:
                                origin_main.type = 'sub'
                                origin_main.save()
                            phone = main_phone_obj.first()
                            phone.type = 'main'
                            phone.save()

                handle_user(instance, group_data, perm_data, profile_data)

        except Exception as e:
            # Log the exception if needed
            error_message = traceback.format_exc().splitlines()[-1]
            app_log.error(f"Error update user: \n{e}\n--- Details: {error_message}")
            # Rollback transaction and re-raise the exception
            # raise ValidationError({'message': f'lỗi bật ngờ khi update user {instance.id}'})
            raise e

        return instance


def handle_user(user, group_data, perm_data, profile_data):
    # Add group to user
    if group_data:
        group_objs = GroupPerm.objects.filter(name__in=group_data)
        missing_groups = list(set(group_data) - set(group_objs.values_list('name', flat=True)))
        if missing_groups:
            raise serializers.ValidationError({'message': f'các groups không tồn tại: {missing_groups}'})
        user.group_user.set(group_objs, through_defaults={'allow': True})

    # Add perm to user
    if perm_data:
        perm_objs = Perm.objects.filter(name__in=perm_data)
        missing_perms = list(set(perm_data) - set(perm_objs.values_list('name', flat=True)))
        if missing_perms:
            raise serializers.ValidationError({'message': f'các perms không tồn tại: {missing_perms}'})
        user.perm_user.set(perm_objs, through_defaults={'allow': True})

    # Handle when user is employee
    if user.user_type == 'employee':
        department_data = profile_data.pop('department', [])
        position_data = profile_data.pop('position', [])
        profile, created = EmployeeProfile.objects.update_or_create(employee_id=user,
                                                                    defaults=profile_data)
        profile.department.set(department_data)
        profile.position.set(position_data)
    # Handle if user is client
    elif user.user_type in ['client', 'farmer']:
        # Get client group id
        client_group_id = profile_data.pop('client_group_id', '')
        # Get client group object
        try:
            client_group = ClientGroup.objects.get(id=client_group_id)
        except ClientGroup.DoesNotExist:
            raise serializers.ValidationError({'message': f'client_group_id {client_group_id} không tồn tại'})
        # Get nvtt id
        nvtt_id = profile_data.pop('nvtt_id', '')
        print(f"Check nvtt_id: {nvtt_id}")
        # Get user as nvtt object
        nv_user = User.objects.filter(id=nvtt_id)
        nvtt = nv_user.filter(
            Q(group_user__name='nvtt') |
            (Q(id=nvtt_id) & Q(user_type='employee') & Q(employeeprofile__position__id='NVTT'))
        ).select_related('employeeprofile').prefetch_related('employeeprofile__position').distinct().first()
        # if nvtt is None and user.user_type == 'client':
        #     raise serializers.ValidationError({'message': f'nvtt {nvtt_id} không tồn tại'})
        print(f"Check nvtt: {nvtt}")
        # Get profile was created with user
        profile, created = ClientProfile.objects.update_or_create(client_id=user, defaults=profile_data)
        # Update profile with data
        profile.client_group_id = client_group
        if nvtt and user.user_type == 'client':
            profile.nvtt_id = nvtt.id
        profile.save()


# Create return response with verify code
def response_verify_code(verify_obj):
    return {
        'id': verify_obj.user.id,
        'phone_number': verify_obj.phone_verify.phone_number,
        'user_type': verify_obj.user.user_type,
        'otp': verify_obj.verify_code,
        'message': f"[DONG XANH] Ma xac thuc cua ban la {verify_obj.verify_code}, tai app Thuoc BVTV Dong Xanh co "
                   f"hieu luc trong 3 phut. Vi ly do bao mat tuyet doi khong cung cap cho bat ky ai."
    }


# Send sms function
def send_sms(phone_number, message):
    app_log.info(f"Sending message OTP")
    url = SMS_SERVICE.get('host')
    # Create all params
    params = {
        'loginName': SMS_SERVICE.get('username'),
        'sign': SMS_SERVICE.get('sign'),
        'serviceTypeId': SMS_SERVICE.get('type'),
        'phoneNumber': phone_number,
        'message': message,
        'brandName': SMS_SERVICE.get('brand'),
    }
    app_log.info(f"Check message: {message}")
    # check url
    request = requests.Request('GET', url, params=params)
    prepared_request = request.prepare()
    full_url = prepared_request.url
    app_log.info(f"Full URL: {full_url}")

    # Make api call
    try:
        response = requests.get(url, params=params)
        app_log.info(f"Response: {response}")
        response.raise_for_status()  # Raise an exception for HTTP errors
    except requests.RequestException as e:
        app_log.error(f"Failed to send SMS: {e}")
        return None

    return response


class EntrustUser(serializers.Serializer):
    user_id = serializers.CharField(required=True)
    time_expire = serializers.TimeField(default=lambda: (datetime.now() + timedelta(hours=2)).time())


class AllowanceOrder(serializers.Serializer):
    manager = serializers.CharField(required=True)
    grant_user = serializers.CharField(required=True)
    is_access = serializers.BooleanField(required=False)
    is_allow = serializers.BooleanField(required=False)
    time_expire = serializers.TimeField(default=lambda: (datetime.now() + timedelta(hours=2)).time())


class GrantAccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = GrantAccess
        fields = ['manager', 'grant_user', 'active', 'allow']
        read_only_fields = ('manager', 'grant_user')


class ViewOtpSerializer(serializers.ModelSerializer):
    class Meta:
        model = Verify
        fields = ['phone_verify', 'is_verify', 'verify_code', 'verify_time', 'created_at', 'updated_at']
