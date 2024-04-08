from django.db import models


# Create your models here.
class UserType(models.Model):
    user_type = models.CharField(max_length=100, unique=True, null=False, blank=False)
    note = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users_type'

    def __str__(self):
        return self.user_type
