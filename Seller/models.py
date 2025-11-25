from django.db import models
from Core.models import User, SubCategory


class Seller(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="seller_profile")
    profile_image = models.ImageField(upload_to='seller_profiles/', null=True, blank=True)
    shop_name = models.CharField(max_length=150)
    address = models.TextField()
    website = models.URLField(null=True, blank=True)


    def __str__(self):
        return self.shop_name


class Product(models.Model):
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE, related_name="products")
    sub_category = models.ForeignKey(SubCategory, on_delete=models.CASCADE, related_name="products")
    product_name = models.CharField(max_length=150)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    slug=models.SlugField()
    rating = models.FloatField(default=0,null=True)
    stock = models.IntegerField(default=0)

    def __str__(self):
        return self.product_name


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    product_img = models.ImageField(upload_to='products/')

    def __str__(self):
        return f"Image for {self.product.product_name}"


