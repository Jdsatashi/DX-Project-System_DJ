from rest_framework import serializers

from account.handlers.restrict_serializer import BaseRestrictSerializer
from user_system.employee_profile.models import Department, Position, EmployeeProfile


class DepartmentSerializer(BaseRestrictSerializer):
    class Meta:
        model = Department
        fields = '__all__'


class PositionSerializer(BaseRestrictSerializer):
    class Meta:
        model = Position
        fields = '__all__'


class EmployeeProfileSerializer(BaseRestrictSerializer):
    class Meta:
        model = EmployeeProfile
        fields = '__all__'


class EmployeeProfileUserSerializer(serializers.ModelSerializer):
    department = serializers.SlugRelatedField(
        many=True,
        slug_field='name',
        queryset=Department.objects.all()
    )
    position = serializers.SlugRelatedField(
        many=True,
        slug_field='name',
        queryset=Position.objects.all()
    )

    class Meta:
        model = EmployeeProfile
        fields = ['fullname', 'address', 'department', 'position']
