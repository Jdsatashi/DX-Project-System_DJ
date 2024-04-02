from django.db import models


# Create your models here.
class UserType(models.Model):
    loaiUser = models.CharField(max_length=100, unique=True, null=False, blank=False)
    mota = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users_type'

    def __str__(self):
        return self.loaiUser
