import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()

from django.contrib.auth import get_user_model

from Core.models import Category, SubCategory
from Seller.models import Seller, Product, ProductImage
from User.models import Customer, Cart, Order, OrderItem, Wishlist, Review, ReviewImage

User = get_user_model()

print("🗑️ Deleting ALL database data...")

# Delete user-generated content first
ReviewImage.objects.all().delete()
Review.objects.all().delete()

OrderItem.objects.all().delete()
Order.objects.all().delete()

Wishlist.objects.all().delete()
Cart.objects.all().delete()

Customer.objects.all().delete()

# Delete product-related
ProductImage.objects.all().delete()
Product.objects.all().delete()

# Delete sellers
Seller.objects.all().delete()

# Delete categories
SubCategory.objects.all().delete()
Category.objects.all().delete()

# Delete all users last (to avoid FK issues)
User.objects.all().delete()

print("✔️ ALL TABLE DATA CLEARED SUCCESSFULLY!")
