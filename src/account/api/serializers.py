import requests
from django.contrib.auth.hashers import make_password
from django.db import transaction, IntegrityError
from rest_framework import serializers

from account.handlers.restrict_serializer import BaseRestrictSerializer
from account.models import User, GroupPerm, Perm, Verify, PhoneNumber
from app.logs import app_log
from app.settings import SMS_SERVICE
from user_system.client_group.models import ClientGroup
from user_system.client_profile.models import ClientProfile
from user_system.employee_profile.models import EmployeeProfile
from utils.constants import maNhomND, status
from utils.helpers import value_or_none, phone_validate, generate_id, generate_digits_code


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


class ClientInfo(serializers.ModelSerializer):
    class Meta:
        model = ClientProfile
        fields = ['register_name', 'organization', 'dob', 'address']


class EmployeeInfo(serializers.ModelSerializer):
    class Meta:
        model = EmployeeProfile
        fields = ['fullname', 'gender', 'dob', 'address']


class UserUpdateSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'region', 'user_type', 'profile']
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
                raise serializers.ValidationError({'phone_number': ['Số điện thoại đã xác thực.']})
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

        return response_verify_code(verify)


class GroupPermSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupPerm
        fields = '__all__'


class PermSerializer(serializers.ModelSerializer):
    class Meta:
        model = Perm
        fields = '__all__'
        read_only_fields = ['name', 'created_at', 'updated_at', 'content_type', 'object_id']


class UserWithPerm(serializers.ModelSerializer):
    group = serializers.ListField(child=serializers.CharField(), write_only=True, required=False, allow_null=True)
    perm = serializers.ListField(child=serializers.CharField(), write_only=True, required=False, allow_null=True)
    phone = serializers.ListField(child=serializers.CharField(), read_only=True, required=False, allow_null=True)

    class Meta:
        model = User
        # fields = '__all__'
        exclude = ['is_staff', 'is_superuser', 'last_login', 'groups', 'user_permissions']
        extra_kwargs = {
            'username': {'required': False},
            'email': {'required': False},
            'password': {'write_only': True}
        }

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['phone'] = [phone.phone_number for phone in instance.phone_numbers.all()]
        return representation

    def create(self, validated_data):
        app_log.info(f"{validated_data}")
        group_data = validated_data.pop('group', None)
        perm_data = validated_data.pop('perm', None)
        phone_data = validated_data.pop('phone', None)

        try:
            with transaction.atomic():
                user = super().create(validated_data)

                # Add group to user
                if group_data:
                    for group in group_data:
                        try:
                            group_obj = GroupPerm.objects.get(name=group)
                        except GroupPerm.DoesNotExist:
                            raise serializers.ValidationError({'group': f'Group id "{group}" does not exist'})
                        user.group_user.add(group_obj, through_defaults={'allow': True})

                # Add perm to user
                if perm_data:
                    for perm in perm_data:
                        try:
                            perm_obj = Perm.objects.get(name=perm)
                        except Perm.DoesNotExist:
                            raise serializers.ValidationError({'perm': f'Perm id "{perm}" does not exist'})
                        user.perm_user.add(perm_obj, through_defaults={'allow': True})

                # Create phone
                if phone_data:
                    for phone_number in phone_data:
                        is_valid, phone_number = phone_validate(phone_number)
                        if not is_valid:
                            raise serializers.ValidationError({'phone': f'Phone number "{phone_number}" is not valid'})
                        try:
                            PhoneNumber.objects.create(phone=phone_number, user=user)
                        except IntegrityError:
                            raise serializers.ValidationError(
                                {'phone': f'Phone number "{phone_number}" already exists'})

        except Exception as e:
            # Log the exception if needed
            app_log.error(f"Error creating user: {e}")
            # Rollback transaction and re-raise the exception
            raise e

        return user

    def update(self, instance, validated_data):
        group_data = validated_data.pop('group', None)
        perm_data = validated_data.pop('perm', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        with transaction.atomic():
            if group_data is not None:
                instance.group_user.clear()
                for group in group_data:
                    try:
                        group_obj = GroupPerm.objects.get(name=group)
                    except GroupPerm.DoesNotExist:
                        raise serializers.ValidationError({'group': f'Group id "{group}" does not exist'})
                    instance.group_user.add(group_obj, through_defaults={'allow': True})
            else:
                instance.group_user.clear()

            if perm_data is not None:
                instance.perm_user.clear()
                for perm in perm_data:
                    try:
                        perm_obj = Perm.objects.get(name=perm)
                    except Perm.DoesNotExist:
                        raise serializers.ValidationError({'perm': f'Perm id "{perm}" does not exist'})
                    instance.perm_user.add(perm_obj, through_defaults={'allow': True})
            else:
                instance.perm_user.clear()

        return instance


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
    # Make api call
    response = requests.get(url, params=params)
    return response
