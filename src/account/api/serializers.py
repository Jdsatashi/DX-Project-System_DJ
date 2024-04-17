import requests
from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from account.models import User, GroupPerm, Perm, Verify
from app.settings import SMS_SERVICE
from user_system.client_group.models import ClientGroup
from user_system.client_profile.models import ClientProfile
from user_system.user_type.models import UserType
from utils.constants import maNhomND, status
from utils.helpers import value_or_none, phone_validate, generate_id, generate_digits_code


# Create user serializer for rest api form
class UserSerializer(serializers.ModelSerializer):
    # Field meta
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone_number', 'region', 'status', 'user_type']
        extra_kwargs = {
            'phone_number': {'required': False},
            'username': {'required': False},
            'email': {'required': False},
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        # Set fields = None/Null when it's blank
        validated_data['username'] = value_or_none(validated_data['username'], '', None)
        validated_data['email'] = value_or_none(validated_data['email'], '', None)
        validated_data['phone_number'] = value_or_none(validated_data['phone_number'], '', None)
        # Get password and encrypting
        pw = validated_data.get('password', validated_data['id'].lower())
        pw_hash = make_password(pw)
        validated_data['password'] = pw_hash

        return super().create(validated_data)


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'phone_number', 'status', 'user_type']
        read_only_fields = ['id', 'status', 'user_type']

    def create(self, validated_data):
        phone_number = validated_data['phone_number']
        if phone_number is None or phone_number == '':
            raise serializers.ValidationError({'phone_number': ['Bạn phải nhập số điện thoại.']})
        # handle here
        is_valid, phone = phone_validate(phone_number)
        if not is_valid:
            raise serializers.ValidationError({'phone_number': ['Số điện thoại không hợp lệ.']})

        # handle create user
        type_kh, _ = UserType.objects.get_or_create(user_type="khachhang")
        user_type = type_kh
        _id = generate_id(maNhomND)
        user = User.objects.create(id=_id, phone_number=phone, user_type=user_type, status=status[1], is_active=False)
        client_group = ClientGroup.objects.get(id=maNhomND)
        client_profile = ClientProfile.objects.create(client_id=user, client_group_id=client_group)
        verify_code = generate_digits_code()
        verify = Verify.objects.create(user=user, verify_code=verify_code, verify_type="SMS OTP")
        result = {
            'id': user.id,
            'phone_number': user.phone_number,
            'user_type': user.user_type.user_type,
        }
        response = send_sms(user.phone_number, result['message'])
        print(response)
        return result


def send_sms(phone_number, message):
    url = SMS_SERVICE.get('host')
    params = {
        'loginName': SMS_SERVICE.get('username'),
        'sign': SMS_SERVICE.get('sign'),
        'serviceTypeId': SMS_SERVICE.get('type'),
        'phoneNumber': phone_number,
        'message': message,
        'brandName': SMS_SERVICE.get('brand'),
    }
    response = requests.get(url, params=params)
    return response


class GroupPermSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupPerm
        fields = '__all__'


class PermSerializer(serializers.ModelSerializer):
    class Meta:
        model = Perm
        fields = '__all__'
