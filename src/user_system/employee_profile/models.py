from django.db import models

from account.models import User


class Department(models.Model):
    id = models.CharField(max_length=50, primary_key=True, unique=True)
    name = models.CharField(max_length=255, null=False, blank=False)
    note = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'employees_department'

    def __str__(self):
        return f"Department: {self.name}"


class Position(models.Model):
    id = models.CharField(max_length=50, primary_key=True, unique=True)
    name = models.CharField(max_length=255, null=False, blank=False)
    note = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'employees_position'

    def __str__(self):
        return f"Position: {self.name}"


class EmployeeProfile(models.Model):
    employee_id = models.OneToOneField(User, to_field='id', null=False, on_delete=models.CASCADE)
    department_id = models.ForeignKey(Department, to_field='id', null=True, blank=False, on_delete=models.SET_NULL)
    position_id = models.ForeignKey(Position, to_field='id', null=True, blank=False, on_delete=models.SET_NULL)
    fullname = models.CharField(max_length=255)
    gender = models.CharField(max_length=1)
    dob = models.DateField(null=True)
    address = models.CharField(max_length=255, null=True)
    created_by = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'employees_profile'
