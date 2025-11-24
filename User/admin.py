from django.contrib import admin
from .models import Customer,Cart,Order,OrderItem,Address,Review,ReviewImage

from User.models import Order, OrderItem, Customer, Review, ReviewImage

# Register your models here.
<<<<<<< HEAD
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Customer)
admin.site.register(Review)
admin.site.register(ReviewImage)
=======

admin.site.register(Customer)
admin.site.register(Cart)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Address)
admin.site.register(Review)
admin.register(ReviewImage)
>>>>>>> 975012024e8fa9c0ef5abb883b4907e10db4c7fb
