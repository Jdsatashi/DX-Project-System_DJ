from django.contrib import admin

from marketing.price_list.models import PriceList, ProductPrice

# Register your models here.
admin.site.register(PriceList)
admin.site.register(ProductPrice)
