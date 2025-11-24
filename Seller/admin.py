from django.contrib import admin





# Register your models here.

from .models import Seller,Product,ProductImage

# Register your models here.


admin.site.register(Seller)
admin.site.register(Product)
admin.site.register(ProductImage)
