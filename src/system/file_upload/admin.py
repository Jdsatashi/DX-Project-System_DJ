from django.contrib import admin

from system.file_upload.models import FileUpload, ProductCateFile, ProductFile, RegistrationCertFile

# Register your models here.
admin.site.register(FileUpload)
admin.site.register(ProductCateFile)
admin.site.register(ProductFile)
admin.site.register(RegistrationCertFile)
