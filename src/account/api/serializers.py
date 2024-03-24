from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from account.models import User


# Create user serializer for rest api form
class UserSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        # Upper all usercode
        email = validated_data.get('email', None)
        phone = validated_data.get('phone_number', None)
        username = validated_data.get('username', None)
        # Set fields = None/Null when it's blank
        validated_data['username'] = username if username != '' else None
        validated_data['email'] = email if email != '' else None
        validated_data['phone_number'] = phone if phone != '' else None
        # Get password and encrypting
        pw = validated_data.get('password', validated_data['usercode'].lower())
        pw_hash = make_password(pw)
        validated_data['password'] = pw_hash

        return super().create(validated_data)

    # Field meta
    class Meta:
        model = User
        fields = ['usercode', 'username', 'email', 'phone_number', 'khuVuc', 'status', 'loaiUser']
        extra_kwargs = {
            'phone_number': {'required': False},
            'username': {'required': False},
            'email': {'required': False},
            'password': {'write_only': True}
        }
