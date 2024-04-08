from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from account.models import User, GroupPerm, Perm
from utils.helpers import value_or_none


# Create user serializer for rest api form
class UserSerializer(serializers.ModelSerializer):
    # Field meta
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone_number', 'khuVuc', 'status', 'loaiUser']
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


class GroupPermSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupPerm
        fields = '__all__'


class PermSerializer(serializers.ModelSerializer):
    class Meta:
        model = Perm
        fields = '__all__'
