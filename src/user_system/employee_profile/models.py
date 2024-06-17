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

    def save(self, *args, **kwargs):
        if not self.id:
            pre_name = self.name.split(" ")
            if len(pre_name) > 2:
                first_char = "".join(word[0].upper() for word in pre_name)[:3]
            elif len(pre_name) == 2:
                first_char = pre_name[0][0].upper() + pre_name[1][:2].upper()
            else:
                first_char = "".join(pre_name[:3])
            new_id = first_char
            counter = 1
            # Loop to find a unique ID
            while Position.objects.filter(id=new_id).exists():
                new_id = f"{first_char}{counter:02d}"
                counter += 1
            self.id = new_id
        super().save(*args, **kwargs)


class EmployeeProfile(models.Model):
    employee_id = models.OneToOneField(User, to_field='id', null=False, on_delete=models.CASCADE)
    department = models.ManyToManyField(Department)
    position = models.ManyToManyField(Position)
    register_name = models.CharField(max_length=255, null=True)
    gender = models.CharField(max_length=1, null=True)
    dob = models.DateField(null=True)
    address = models.CharField(max_length=255, null=True)
    created_by = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'employees_profile'
