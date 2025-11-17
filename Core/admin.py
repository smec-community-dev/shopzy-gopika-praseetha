from django.contrib import admin

from Core.models import User, Category, SubCategory

# Register your models here.
admin.site.register(User)
admin.site.register(Category)
admin.site.register(SubCategory)