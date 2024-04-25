from django.contrib import admin

from marketing.product.models import Product, ProductType, RegistrationUnit, Producer, RegistrationCert, \
    ProductCategory, CategoryDetail

# Register your models here.
admin.site.register(ProductType)
admin.site.register(RegistrationUnit)
admin.site.register(Producer)
admin.site.register(RegistrationCert)
admin.site.register(ProductCategory)
admin.site.register(Product)
admin.site.register(CategoryDetail)
