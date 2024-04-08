from django.contrib import admin
from user_system.employee_profile.models import EmployeeProfile, Department, Position


# Register your models here.
admin.site.register(Position)
admin.site.register(Department)
admin.site.register(EmployeeProfile)
