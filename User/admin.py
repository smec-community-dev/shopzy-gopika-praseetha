from django.contrib import admin

from User.models import Order, OrderItem, Customer, Review, ReviewImage

# Register your models here.
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Customer)
admin.site.register(Review)
admin.site.register(ReviewImage)