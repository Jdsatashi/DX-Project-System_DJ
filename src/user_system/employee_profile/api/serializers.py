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
