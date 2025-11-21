from datetime import timedelta
from datetime import datetime, timedelta
from django.db.models.functions import TruncMonth, TruncWeek, TruncDay
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth, TruncYear
from datetime import datetime, timedelta
import json

from django.contrib.auth.decorators import login_required
from django.core.mail import message
from django.core.paginator import Paginator
from django.db.models import Sum, Avg, Prefetch, F, Count

from django.shortcuts import render,redirect
from django.template.defaultfilters import date
from django.utils import timezone
from django.utils.text import slugify
from django.utils.timezone import now

from Core.models import User, SubCategory
from User.models import Order, OrderItem, Review
from decorators.decorators import role_required
from .models import Seller, Product, ProductImage
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth import authenticate, login
from django.contrib import messages

# Create your views here.

from django.contrib import messages

def user_register(request):
    if request.method == "POST":


        required = ['username', 'email', 'password', 'contact', 'shop_name', 'address']
        for field in required:
            if not request.POST.get(field):
                messages.error(request, f"{field.replace('_',' ').title()} is required")
                return redirect('seller_register')

        seller = User()
        seller.username = request.POST.get('username')
        seller.email = request.POST.get('email')
        seller.password = request.POST.get('password')
        seller.set_password(request.POST.get('password'))
        seller.contact = request.POST.get('contact')
        seller.role = "seller"
        seller.save()

        seller_user = Seller()
        seller_user.user = seller
        seller_user.shop_name = request.POST.get('shop_name')
        seller_user.image = request.POST.get('profile_img')
        seller_user.website = request.POST.get('website')
        seller_user.address = request.POST.get('address')
        seller_user.save()

        messages.success(request, "Registration successful!")
        return redirect('seller_login')

    return render(request,'seller/seller_register.html')


@login_required(login_url='seller/login')
@role_required("seller", login_url="/seller/login")
def seller_dashboard(request):
    seller = Seller.objects.get(user=request.user)

    products = Product.objects.filter(seller=seller)
    total_products = products.count()
    order_items = OrderItem.objects.filter(product__seller=seller)
    order = OrderItem.objects.filter(product__seller=seller)
    total_order = order.count()
    orders = OrderItem.objects.filter(product__seller=seller).order_by('-id')

    # Corrected top_products query
    top_products = (
        Product.objects
        .filter(seller=seller)
        .annotate(
            total_qty_sold=Sum('orderitem__quantity'),
            average_rating=Avg('reviews__rating')
        )
        .prefetch_related(
            Prefetch(
                'images',
                queryset=ProductImage.objects.order_by('id'),
                to_attr='product_images'
            )
        )
        .order_by('-total_qty_sold')[:5]
    )

    reviews = Review.objects.filter(product__seller=seller).prefetch_related(
        Prefetch('reviewimage_set', to_attr='images')
    ).order_by('-id')
    conversion_rate = (total_order / total_products * 100) if total_products else 0


    customer_satisfaction = reviews.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0


    total_stock = products.aggregate(stock_sum=Sum('stock'))['stock_sum'] or 0
    sold_stock = order_items.aggregate(sold_sum=Sum('quantity'))['sold_sum'] or 0
    inventory_turnover = (sold_stock / (sold_stock + total_stock) * 100) if (sold_stock + total_stock) else 0

    # Average Order Value (AOV)
    total_revenue = order_items.annotate(price=F('product__price') * F('quantity')).aggregate(total=Sum('price'))[
                        'total'] or 0
    avg_order_value = (total_revenue / total_order) if total_order > 0 else 0

    # Repeat Customers (%)
    customers_order_counts = Order.objects.filter(order_items__product__seller=seller).values('user').annotate(
        orders_count=Count('id')
    )

    repeat_customers = sum(1 for c in customers_order_counts if c['orders_count'] > 1)
    total_customers = customers_order_counts.count()

    repeat_customers_percentage = (repeat_customers / total_customers * 100) if total_customers else 0

    # Stock Alert (products with stock < 5)
    low_stock_count = products.filter(stock__lt=5).count()

    # Temporary Response Time (until chat system added)
    response_time = "N/A"
    average_rating = reviews.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0

    # Revenue Calculation
    total_revenue = order_items.annotate(
        revenue=F('product__price') * F('quantity')
    ).aggregate(total=Sum('revenue'))['total'] or 0

    return render(request, 'seller/seller_dashboard.html', {
        'products': products,
        'total_products': total_products,
        'total_order': total_order,
        'top_products': top_products,
        'reviews': reviews,
        'seller': seller,
        'orders': orders,
        'conversion_rate': round(conversion_rate, 1),
        'customer_satisfaction': round(customer_satisfaction, 1),
        'inventory_turnover': round(inventory_turnover, 1),
        'avg_order_value': round(avg_order_value, 2),
        'repeat_customers_percentage': round(repeat_customers_percentage, 1),
        'response_time': response_time,
        'low_stock_count': low_stock_count,
        'average_rating': round(average_rating, 1),
        'total_revenue': round(total_revenue, 2),



    })


def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, "Invalid username or password")
            return redirect("seller_login")

        if user.role != "seller":
            messages.error(request, "You are not a seller")
            return redirect("seller_login")

        login(request, user)
        return redirect("seller_dashboard")

    return render(request, "seller/seller_login.html")

@login_required(login_url='/seller/login')
@role_required("seller", login_url="/seller/login")
def Create_Product(request):
    subcategories = SubCategory.objects.all()
    print(subcategories)
    seller = Seller.objects.get(user=request.user)
    products = Product.objects.filter(seller=seller)
    paginator = Paginator(products, 10)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    if request.method == "POST":
        product = Product()


        product.seller = seller

        product.sub_category_id = request.POST.get("subcategory_id")
        product.product_name = request.POST.get("product_name")
        product.price = request.POST.get("price")
        product.description = request.POST.get("description")
        product.slug = slugify(product.product_name)
        product.rating = request.POST.get("rating")
        product.stock = request.POST.get("stock")
        product.save()

        image = request.FILES.get("image")
        print("imagefound")
        if image:
            ProductImage.objects.create(product=product, product_img=image)

        return redirect('/seller/product')

    return render(request, 'seller/seller_addproduct.html', {
        'subcategories': subcategories,
        'products': products,
    })
@login_required(login_url='/seller/login')
@role_required("seller", login_url="/seller/login")
def product_delete(request, slug):
    try:
        product = Product.objects.get(slug=slug, seller__user=request.user)
        product.delete()
    except Product.DoesNotExist:
        return redirect('/seller/product')  # if product not found, just redirect

    return redirect('/seller/product')


@login_required(login_url='/seller/login')
@role_required("seller", login_url="/seller/login")
def edit_product(request, slug):
    product = Product.objects.get(slug=slug)
    subcategories = SubCategory.objects.all()

    if request.method == "POST":
        product.sub_category_id = request.POST.get("subcategory_id")
        product.product_name = request.POST.get("product_name")
        product.price = request.POST.get("price")
        product.description = request.POST.get("description")
        product.slug = request.POST.get("slug")
        product.rating = request.POST.get("rating")
        product.stock = request.POST.get("stock")
        product.save()

        image = request.FILES.get("image")
        if image:
            ProductImage.objects.create(product=product, product_img=image)

        return redirect('/seller/product')

    return render(request, 'seller/seller_editproduct.html', {
        'product': product,
        'subcategories': subcategories,
    })
@login_required(login_url='/seller/login')
@role_required("seller", login_url="/seller/login")
def order_list(request):
    seller = Seller.objects.get(user=request.user)


    order_items = OrderItem.objects.filter(product__seller=seller).select_related('order', 'product')

    paginator = Paginator(order_items, 10)
    page_number = request.GET.get('page')
    orders = paginator.get_page(page_number)

    return render(request, 'seller/seller_orders.html', {
        'orders': orders
    })
def order_single_list(request, id):
    seller = Seller.objects.get(user=request.user)
    order = OrderItem.objects.get(id=id, product__seller=seller)
    print(order)
    print(id)
    return render(request, 'seller/seller_order_single.html', {'order': order})
def product_single(request,slug):
    product=Product.objects.get(slug=slug)
    review=Review.objects.filter(product=product)
    print(review)
    return render(request,'seller/product_details.html',{'product':product,'review':review})
# def product_all(request):
#     seller=Seller.objects.filter(seller=request.user)
#     reviews = Review.objects.filter(product__seller=seller).prefetch_related(
#         Prefetch('reviewimage_set', to_attr='images')
#     ).order_by('-id')

def seller_profile(request):
    seller=Seller.objects.get(user=request.user)
    print(seller)
    return render(request,'seller/seller_profile.html',{'seller':seller})
def seller_forgott(request):
    return render(request,'seller/seller_forgott.html')
@login_required(login_url='/seller/login')
@role_required("seller", login_url="/seller/login")
def seller_logout(request):

    logout(request)
    return redirect('seller_login')