import os

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.timezone import now

from app.logs import app_log
from marketing.product.models import ProductCategory, Product, RegistrationCert


def upload_location(filename):
    now_time = now()
    year = str(now_time.year)
    month = '{:02d}'.format(now_time.month)
    app_log.info(f"Expect path: \"uploads/{year}/{month}/{filename}\"")
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

    def __str__(self):
        return f"({str(self.id)}) : '{str(self.file)}'"


class ProductCateFile(models.Model):
    file = models.ForeignKey(FileUpload, null=True, on_delete=models.SET_NULL, related_name='product_cate_files')
    product_cate = models.ForeignKey(ProductCategory, null=True, on_delete=models.SET_NULL, related_name='product_cate_files')
    priority = models.IntegerField(default=1)
    note = models.CharField(max_length=255, null=True, blank=True)
    created_by = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        product_cate_file = ProductCateFile.objects.filter(product_cate=self.product_cate)
        if product_cate_file.exists() and self.id not in product_cate_file.values_list('id', flat=True):
            prio_list = [p.priority for p in product_cate_file]
            if self.priority in prio_list:
                self.priority = max(prio_list) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"({str(self.product_cate)}) : '{str(self.file.file_name)}'"


class ProductFile(models.Model):
    file = models.ForeignKey(FileUpload, null=True, on_delete=models.SET_NULL, related_name='product_files')
    product = models.ForeignKey(Product, null=True, on_delete=models.SET_NULL, related_name='product_files')
    priority = models.IntegerField(default=1)
    note = models.CharField(max_length=255, null=True, blank=True)
    created_by = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        product_file = ProductFile.objects.filter(product=self.product)
        if product_file.exists() and self.id not in product_file.values_list('id', flat=True):
            prio_list = [p.priority for p in product_file]
            if self.priority in prio_list:
                self.priority = max(prio_list) + 1
        super().save(*args, **kwargs)


class RegistrationCertFile(models.Model):
    file = models.ForeignKey(FileUpload, on_delete=models.CASCADE)
    register_cert = models.ForeignKey(RegistrationCert, null=True, on_delete=models.SET_NULL)
    priority = models.IntegerField(default=1)
    note = models.CharField(max_length=255, null=True, blank=True)
    created_by = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"({str(self.register_cert)}) : '{str(self.file.file)}'"

    def save(self, *args, **kwargs):
        register_file = RegistrationCertFile.objects.filter(register_cert=self.register_cert)
        if register_file.exists() and self.id not in register_file.values_list('id', flat=True):
            prio_list = [p.priority for p in register_file]
            if self.priority in prio_list:
                self.priority = max(prio_list) + 1
        super().save(*args, **kwargs)


class ContentFile(models.Model):
    file = models.ForeignKey(FileUpload, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=255)
    content_object = GenericForeignKey('content_type', 'object_id')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"({str(self.content_type)} - {str(self.object_id)}) : '{str(self.file.file)}'"

    def save(self, *args, **kwargs):
        if ContentFile.objects.filter(file=self.file, content_type=self.content_type, object_id=self.object_id).exists():
            raise Exception("File already exists in this content")
        super().save(*args, **kwargs)
