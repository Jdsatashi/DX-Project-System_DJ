from django.db import models


# Create your models here.
class GroupDraft(models.Model):
    name = models.CharField(unique=True, blank=False, null=False)
    level = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Draft(models.Model):
    title = models.CharField(max_length=124, unique=True, blank=False, null=False)
    content = models.CharField()
    purpose = models.CharField()
    no = models.IntegerField(default=1)
    group = models.ManyToManyField(GroupDraft)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
