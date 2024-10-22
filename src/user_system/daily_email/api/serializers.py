from django.db import transaction
from rest_framework import serializers

from account.models import User
from app import settings
from app.logs import app_log
from user_system.daily_email.models import UserGetMail, EmailDetail
from utils.helpers import check_email


class EmailDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailDetail
        fields = '__all__'


class UserGetMailSerializer(serializers.ModelSerializer):
    email = serializers.CharField(allow_null=True, required=False, write_only=True)

    class Meta:
        model = UserGetMail
        fields = '__all__'
        read_only_fields = ('last_sent', 'created_at')
        extra_kwargs = {
            'user': {'allow_null': True, 'required': False},
        }

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['email'] = instance.user.email
        return representation

    def create(self, validate_data):
        try:
            with transaction.atomic():
                email = validate_data.pop('email', None)
                user = validate_data.get('user', None)
                app_log.info(f"Test input data: {email} - {user}")

                if user is None and email is None:
                    raise serializers.ValidationError({'message': 'required email or user id'})
                if email:
                    user_mail = User.objects.filter(email=email).first()
                    if not user_mail:
                        raise serializers.ValidationError({'message': 'email not exists'})
                    validate_data['user'] = user_mail
                obj = UserGetMail.objects.create(**validate_data)
                return obj
        except Exception as e:
            raise e


class SendReportMailSerializer(serializers.Serializer):
    email = serializers.ListField(
        child=serializers.CharField(),
        required=True
    )
    date_get = serializers.DateField(required=False)

    def validate_email(self, value):
        for email in value:
            email_valid = check_email(email)
            if not email_valid:
                raise serializers.ValidationError({'message': f'email {email} không hợp lệ'})
        return value
