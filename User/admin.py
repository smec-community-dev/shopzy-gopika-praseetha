from django.contrib import admin
from .models import Customer,Cart,Order,OrderItem,Address,Review,ReviewImage

# Register your models here.

admin.site.register(Customer)
admin.site.register(Cart)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Address)
admin.site.register(Review)
admin.register(ReviewImage)
