from rest_framework import serializers

from user_system.daily_email.models import UserGetMail, EmailDetail
from utils.helpers import check_email


class EmailDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailDetail
        fields = '__all__'


class UserGetMailSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserGetMail
        fields = '__all__'


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
