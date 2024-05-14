import requests
from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from account.models import User, GroupPerm, Perm, Verify, PhoneNumber
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


# Create reeturn response with verify code
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


class GroupPermSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupPerm
        fields = '__all__'


class PermSerializer(serializers.ModelSerializer):
    class Meta:
        model = Perm
        fields = '__all__'
