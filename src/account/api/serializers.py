import requests
from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from account.models import User, GroupPerm, Perm, Verify, PhoneNumber
from app.settings import SMS_SERVICE
from user_system.client_group.models import ClientGroup
from user_system.client_profile.models import ClientProfile
from user_system.user_type.models import UserType
from utils.constants import maNhomND, status
from utils.helpers import value_or_none, phone_validate, generate_id, generate_digits_code


class PhoneNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhoneNumber
        fields = ['phone_number']


# Create user serializer for rest api form
class UserSerializer(serializers.ModelSerializer):
    # phone_number = PhoneNumberSerializer(allow_null=False)

    # Field meta
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'region', 'status', 'user_type']
        extra_kwargs = {
            'username': {'required': False},
            'email': {'required': False},
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        # Set fields = None/Null when it's blank
        validated_data['username'] = value_or_none(validated_data['username'], '', None)
        validated_data['email'] = value_or_none(validated_data['email'], '', None)
        phone_number = validated_data.pop(validated_data['phone_number'], '', None)
        # Get password and encrypting
        pw = validated_data.get('password', validated_data['id'].lower())
        pw_hash = make_password(pw)
        validated_data['password'] = pw_hash

        return super().create(validated_data)


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
        phone = PhoneNumber.objects.filter(phone_number=phone)
        print("Here -------------")
        verify_code = generate_digits_code()
        # When phone Existed but not verify
        if phone.exists():
            phone_num = phone.first()
            user = phone_num.user
            verify = Verify.objects.filter(phone_verify=phone_num, is_verify=False)
            # If verified, raise error
            if not verify.exists():
                raise serializers.ValidationError({'phone_number': ['Số điện thoại đã xác thực.']})
            verify = verify.first()
            verify.get_new_code(verify_code)
        else:
            # Handle create user
            type_kh, _ = UserType.objects.get_or_create(user_type="client")
            user_type = type_kh
            _id = generate_id(maNhomND)
            user = User.objects.create(id=_id, user_type=user_type, status=status[1], is_active=False)
            phone = PhoneNumber.objects.create(phone_number=phone_number, user=user)
            client_group = ClientGroup.objects.get(id=maNhomND)
            client_profile = ClientProfile.objects.create(client_id=user, client_group_id=client_group)
            verify = Verify.objects.create(user=user, phone_verify=phone, verify_code=verify_code,
                                           verify_type="SMS OTP")
        print(verify)
        return create_verify_code(verify)


def create_verify_code(verify_obj):
    return {
        'id': verify_obj.user.id,
        'phone_number': verify_obj.phone_verify.phone_number,
        'user_type': verify_obj.user.user_type.user_type,
        'otp': verify_obj.verify_code,
        'message': f"[DONG XANH] Ma xac thuc cua ban la {verify_obj.verify_code}, tai app Thuoc BVTV Dong Xanh co "
                   f"hieu luc trong 3 phut. Vi ly do bao mat tuyet doi khong cung cap cho bat ky ai."
    }


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
