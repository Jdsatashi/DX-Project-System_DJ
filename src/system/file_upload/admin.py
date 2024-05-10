from django.contrib import admin

from system.file_upload.models import FileUpload, ProductCateFile, ProductFile, RegistrationCertFile


class FileUploadAmin(admin.ModelAdmin):
    search_fields = ['file', 'file_name']


# Register your models here.
admin.site.register(FileUpload, FileUploadAmin)
admin.site.register(ProductCateFile)
admin.site.register(ProductFile)
admin.site.register(RegistrationCertFile)
