import os

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.timezone import now


def upload_location(instance, filename, model):
    model_name = instance.__class__.__name__.lower()
    now_time = now()
    year = str(now_time.year)
    month = '{:02d}'.format(now_time.month)
    print(f"Expect path: \"uploads/{model_name}/{year}/{month}/{filename}\"")
    # return f"uploads/{model_name}/{now_time.year}/{now_time.month}/{filename}"
    return os.path.join('uploads', model, year, month, filename)


# Create your models here.
class FileUpload(models.Model):
    label = models.CharField(max_length=255)
    file = models.FileField()
    file_name = models.CharField(max_length=255, unique=True, null=False, blank=False)
    file_ext = models.CharField(max_length=12, null=False, blank=True)
    note = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    content_type = models.ForeignKey(ContentType, null=True, on_delete=models.SET_NULL)
    object_id = models.CharField(max_length=255, null=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    def save(self, *args, **kwargs):
        if self.file:
            # Get name and extension of file
            basename, file_ext = os.path.splitext(self.file.name)
            filename = basename.split('/')[-1]
            # Create new filename to validate if filename exists
            new_file_name = filename
            i = 1
            # Check if filename already exists
            while FileUpload.objects.filter(file_name=new_file_name).exists():
                # Add i = 1, 2, 3... number to filename
                new_file_name = f"{filename}_{i}"
                i += 1
            # Update filename and extension
            self.file_name = new_file_name
            self.file_ext = file_ext
            # Get model from content type
            model = self.content_type.model
            if not self.label:
                self.label = self.file_name
            self.file.name = upload_location(self, self.file_name + file_ext, model)
        super().save(*args, **kwargs)
