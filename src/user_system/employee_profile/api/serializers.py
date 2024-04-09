from account.handlers.restrict_serializer import BaseRestrictSerializer
from user_system.employee_profile.models import Department, Position, EmployeeProfile


class DepartmentSerializer(BaseRestrictSerializer):
    model = Department
    fields = '__all__'


class PositionSerializer(BaseRestrictSerializer):
    model = Position
    fields = '__all__'


class EmployeeProfileSerializer(BaseRestrictSerializer):
    model = EmployeeProfile
    fields = '__all__'
