import os

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.timezone import now


def upload_location(filename):
    now_time = now()
    year = str(now_time.year)
    month = '{:02d}'.format(now_time.month)
    print(f"Expect path: \"uploads/{year}/{month}/{filename}\"")
    # return f"uploads/{model_name}/{now_time.year}/{now_time.month}/{filename}"
    return os.path.join('uploads', year, month, filename)


def check_ext(ext):
    image_extensions = ['.jpg', '.jpeg', '.png']
    document_extensions = ['.pdf', '.docx', '.xlsx', '.pptx']
    if ext in image_extensions:
        return 'image'
    if ext in document_extensions:
        return 'document'


# Create your models here.
class FileUpload(models.Model):
    file = models.FileField(unique=True)
    file_name = models.CharField(max_length=255, unique=True, null=False, blank=True)
    file_ext = models.CharField(max_length=12, null=False, blank=True)
    type = models.CharField(max_length=8, null=True, choices=(('document', 'Document'), ('image', 'Image')))
    order = models.IntegerField(default=1)
    note = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
            self.type = check_ext(self.file_ext)
            self.file.name = upload_location(self.file_name + file_ext)
        super().save(*args, **kwargs)


class ContentFile(models.Model):
    file = models.ForeignKey(FileUpload, to_field='file', on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=255)
    content_object = GenericForeignKey('content_type', 'object_id')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
