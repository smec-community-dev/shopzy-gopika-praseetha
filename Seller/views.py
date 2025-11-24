
from datetime import timedelta
from datetime import datetime, timedelta

from django.contrib.auth.forms import PasswordChangeForm
from django.db.models.functions import TruncMonth, TruncWeek, TruncDay
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth, TruncYear
from datetime import datetime, timedelta
import json

from django.contrib.auth.decorators import login_required
from django.core.mail import message
from django.core.paginator import Paginator
from django.db.models import Sum, Avg, Prefetch, F, Count, Q
from django.http import JsonResponse

from django.shortcuts import render, redirect, get_object_or_404
from datetime import date, timedelta
import calendar
from django.utils import timezone
from django.utils.text import slugify
from django.utils.timezone import now

from Core.models import User, SubCategory
from User.models import Order, OrderItem, Review
from decorators.decorators import role_required
from .models import Seller, Product, ProductImage
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
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



# def seller_dashboard(request):
#     seller = Seller.objects.get(user=request.user)
#
#     products = Product.objects.filter(seller=seller)
#     total_products = products.count()
#     order_items = OrderItem.objects.filter(product__seller=seller)
#     order = OrderItem.objects.filter(product__seller=seller)
#     total_order = order.count()
#     orders = OrderItem.objects.filter(product__seller=seller).order_by('-id')
#
#     # Corrected top_products query
#     top_products = (
#         Product.objects
#         .filter(seller=seller)
#         .annotate(
#             total_qty_sold=Sum('orderitem__quantity'),
#             average_rating=Avg('reviews__rating')
#         )
#         .prefetch_related(
#             Prefetch(
#                 'images',
#                 queryset=ProductImage.objects.order_by('id'),
#                 to_attr='product_images'
#             )
#         )
#         .order_by('-total_qty_sold')[:5]
#     )
#
#     reviews = Review.objects.filter(product__seller=seller).prefetch_related(
#         Prefetch('reviewimage_set', to_attr='images')
#     ).order_by('-id')
#     conversion_rate = (total_order / total_products * 100) if total_products else 0
#
#
#     customer_satisfaction = reviews.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0
#
#
#     total_stock = products.aggregate(stock_sum=Sum('stock'))['stock_sum'] or 0
#     sold_stock = order_items.aggregate(sold_sum=Sum('quantity'))['sold_sum'] or 0
#     inventory_turnover = (sold_stock / (sold_stock + total_stock) * 100) if (sold_stock + total_stock) else 0
#
#     # Average Order Value (AOV)
#     total_revenue = order_items.annotate(price=F('product__price') * F('quantity')).aggregate(total=Sum('price'))[
#                         'total'] or 0
#     avg_order_value = (total_revenue / total_order) if total_order > 0 else 0
#
#     # Repeat Customers (%)
#     customers_order_counts = Order.objects.filter(order_items__product__seller=seller).values('user').annotate(
#         orders_count=Count('id')
#     )
#
#     repeat_customers = sum(1 for c in customers_order_counts if c['orders_count'] > 1)
#     total_customers = customers_order_counts.count()
#
#     repeat_customers_percentage = (repeat_customers / total_customers * 100) if total_customers else 0
#
#     # Stock Alert (products with stock < 5)
#     low_stock_count = products.filter(stock__lt=5).count()
#
#     # Temporary Response Time (until chat system added)
#     response_time = "N/A"
#     average_rating = reviews.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0
#
#     # Revenue Calculation
#     total_revenue = order_items.annotate(
#         revenue=F('product__price') * F('quantity')
#     ).aggregate(total=Sum('revenue'))['total'] or 0
#
#     return render(request, 'seller/seller_dashboard.html', {
#         'products': products,
#         'total_products': total_products,
#         'total_order': total_order,
#         'top_products': top_products,
#         'reviews': reviews,
#         'seller': seller,
#         'orders': orders,
#         'conversion_rate': round(conversion_rate, 1),
#         'customer_satisfaction': round(customer_satisfaction, 1),
#         'inventory_turnover': round(inventory_turnover, 1),
#         'avg_order_value': round(avg_order_value, 2),
#         'repeat_customers_percentage': round(repeat_customers_percentage, 1),
#         'response_time': response_time,
#         'low_stock_count': low_stock_count,
#         'average_rating': round(average_rating, 1),
#         'total_revenue': round(total_revenue, 2),
#
#
#
#     })
@login_required(login_url='seller/login')
@role_required("seller", login_url="/seller/login")
def seller_dashboard(request):
    seller = Seller.objects.get(user=request.user)

    products = Product.objects.filter(seller=seller)
    total_products = products.count()
    order_items = OrderItem.objects.filter(product__seller=seller)
    total_order = order_items.count()
    orders = OrderItem.objects.filter(product__seller=seller).order_by('-id')[:5]

    # Top products query
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
    ).order_by('-id')[:5]

    conversion_rate = (total_order / total_products * 100) if total_products else 0
    customer_satisfaction = reviews.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0

    total_stock = products.aggregate(stock_sum=Sum('stock'))['stock_sum'] or 0
    sold_stock = order_items.aggregate(sold_sum=Sum('quantity'))['sold_sum'] or 0
    inventory_turnover = (sold_stock / (sold_stock + total_stock) * 100) if (sold_stock + total_stock) else 0

    # Revenue calculations
    total_revenue = order_items.annotate(
        revenue=F('product__price') * F('quantity')
    ).aggregate(total=Sum('revenue'))['total'] or 0
    avg_order_value = (total_revenue / total_order) if total_order > 0 else 0

    # Repeat Customers
    customers_order_counts = Order.objects.filter(order_items__product__seller=seller).values('user').annotate(
        orders_count=Count('id')
    )
    repeat_customers = sum(1 for c in customers_order_counts if c['orders_count'] > 1)
    total_customers = customers_order_counts.count()
    repeat_customers_percentage = (repeat_customers / total_customers * 100) if total_customers else 0

    # Business alerts
    low_stock_count = products.filter(stock__lt=5).count()
    response_time = "2.5 hrs"
    average_rating = reviews.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0

    # **CORRECTED: Weekly Sales Data (Last 7 days)**
    weekly_sales = []
    for i in range(6, -1, -1):
        date = timezone.now() - timedelta(days=i)
        day_sales = OrderItem.objects.filter(
            product__seller=seller,
            order__order_date__date=date.date()
        ).aggregate(
            total=Sum(F('product__price') * F('quantity'))
        )['total'] or 0
        weekly_sales.append({
            'day': date.strftime('%a'),  # Mon, Tue, etc.
            'sales': float(day_sales),
            'full_date': date.strftime('%b %d')  # Jan 15, etc.
        })

    # **CORRECTED: Monthly Sales Data (Last 30 days - properly calculated)**
    monthly_sales = []
    today = timezone.now().date()

    # Get sales for last 30 days, grouped by week
    for week_num in range(4):
        week_end = today - timedelta(days=week_num * 7)
        week_start = week_end - timedelta(days=6)

        week_sales = OrderItem.objects.filter(
            product__seller=seller,
            order__order_date__date__range=[week_start, week_end]
        ).aggregate(
            total=Sum(F('product__price') * F('quantity'))
        )['total'] or 0

        monthly_sales.append({
            'week': f'Week {4 - week_num}',
            'sales': float(week_sales),
            'date_range': f'{week_start.strftime("%m/%d")}-{week_end.strftime("%m/%d")}'
        })

    # Reverse to show chronological order
    monthly_sales.reverse()

    # **CORRECTED: Yearly Sales Data (Current year, all months)**
    yearly_sales = []
    current_year = timezone.now().year

    for month in range(1, 13):
        month_sales = OrderItem.objects.filter(
            product__seller=seller,
            order__order_date__year=current_year,
            order__order_date__month=month
        ).aggregate(
            total=Sum(F('product__price') * F('quantity'))
        )['total'] or 0

        yearly_sales.append({
            'month': datetime(current_year, month, 1).strftime('%b'),  # Jan, Feb, etc.
            'sales': float(month_sales)
        })

    # Calculate max values for proper chart scaling
    weekly_sales_max = max([day['sales'] for day in weekly_sales]) if weekly_sales else 1
    monthly_sales_max = max([week['sales'] for week in monthly_sales]) if monthly_sales else 1
    yearly_sales_max = max([month['sales'] for month in yearly_sales]) if yearly_sales else 1

    context = {
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
        'weekly_sales': weekly_sales,
        'monthly_sales': monthly_sales,
        'yearly_sales': yearly_sales,
        'weekly_sales_max': weekly_sales_max,
        'monthly_sales_max': monthly_sales_max,
        'yearly_sales_max': yearly_sales_max,
        'current_year': current_year,


    }

    return render(request, 'seller/seller_dashboard.html', context)

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



    return render(request, 'seller/seller_addproduct.html', {
        'seller':seller,
        'subcategories': subcategories,
        'products': products,
    })
@login_required(login_url='seller/login')
@role_required("seller", login_url="/seller/login")
def Create_products_form(request):
    subcategories = SubCategory.objects.all()
    seller = Seller.objects.get(user=request.user)
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
    return render(request,'seller/add_form.html', {'subcategories': subcategories,'seller':seller})
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
    seller = Seller.objects.get(user=request.user)
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
        'seller':seller,
    })
@login_required(login_url='/seller/login')
@role_required("seller", login_url="/seller/login")
# def order_list(request):
#     seller = Seller.objects.get(user=request.user)
#
#
#     order_items = OrderItem.objects.filter(product__seller=seller).select_related('order', 'product')
#
#     paginator = Paginator(order_items, 10)
#     page_number = request.GET.get('page')
#     orders = paginator.get_page(page_number)
#
#     return render(request, 'seller/seller_orders.html', {
#         'orders': orders
#     })
@login_required(login_url='seller/login')
@role_required("seller", login_url="/seller/login")
def order_list(request):
    seller = Seller.objects.get(user=request.user)

    # Base queryset
    order_items = OrderItem.objects.filter(product__seller=seller).select_related('order', 'product')

    # Handle search
    search_query = request.GET.get('search', '')
    if search_query:
        order_items = order_items.filter(
            Q(order__user__username__icontains=search_query) |
            Q(product__product_name__icontains=search_query) |
            Q(order__shipping_address__icontains=search_query)
        )

    # Handle status filter
    status_filter = request.GET.get('status', '')
    if status_filter:
        order_items = order_items.filter(order__status=status_filter.lower())

    # Calculate stats for the cards
    total_orders = order_items.count()
    placed_orders = order_items.filter(order__status='placed').count()
    completed_orders = order_items.filter(order__status='delivered').count()
    processing_orders = order_items.filter(order__status='processing').count()

    # Calculate total revenue
    total_revenue = order_items.aggregate(
        total=Sum('order__total_amount')
    )['total'] or 0

    # Pagination
    paginator = Paginator(order_items, 10)
    page_number = request.GET.get('page')
    orders = paginator.get_page(page_number)

    return render(request, 'seller/seller_orders.html', {
        'orders': orders,
        'total_orders': total_orders,
        'placed_orders': placed_orders,
        'completed_orders': completed_orders,
        'processing_orders': processing_orders,
        'total_revenue': total_revenue,
        'current_status_filter': status_filter,
        'search_query': search_query,
        'seller':seller,
    })


@login_required(login_url='seller/login')
@role_required("seller", login_url="/seller/login")

def order_single_list(request, id):
    seller = Seller.objects.get(user=request.user)

    order = get_object_or_404(
        OrderItem.objects.select_related(
            'order',
            'product',
            'order__user',
            'product__sub_category'
        ).prefetch_related(
            Prefetch(
                'product__images',
                queryset=ProductImage.objects.all(),
                to_attr='product_images'
            )
        ),
        id=id,
        product__seller=seller
    )


    order_statuses = ['placed', 'processing', 'shipped', 'delivered']

    # Pass the list to the template context
    context = {
        'order': order,
        'order_statuses': order_statuses,
        'seller':seller,
    }

    return render(request, 'seller/seller_order_single.html', context)


# Note: update_order_status view remains unchanged and correct.
@login_required(login_url='seller/login')
@role_required("seller", login_url="/seller/login")
def update_order_status(request, order_id):

    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')

        # Validate status transition
        valid_statuses = ['placed', 'processing', 'shipped', 'delivered']
        if new_status in valid_statuses:
            order.status = new_status
            order.save()
            messages.success(request, f'Order status updated to {new_status}.')
        else:
            messages.error(request, 'Invalid status.')

        return redirect('orderlist_single', id=order_id)
# def order_single_list(request, id):
#     seller = Seller.objects.get(user=request.user)
#     order = OrderItem.objects.get(id=id, product__seller=seller)
#     print(order)
#     print(id)
#     return render(request, 'seller/seller_order_single.html', {'order': order})
# def product_single(request,slug):
#     product=Product.objects.get(slug=slug)
#     review=Review.objects.filter(product=product)
#     print(review)
#     return render(request,'seller/product_details.html',{'product':product,'review':review})
# def product_all(request):
#     seller=Seller.objects.filter(seller=request.user)
#     reviews = Review.objects.filter(product__seller=seller).prefetch_related(
#         Prefetch('reviewimage_set', to_attr='images')
#     ).order_by('-id')
@login_required(login_url='seller/login')
@role_required("seller", login_url="/seller/login")
def product_single(request, slug):
    product = Product.objects.get(slug=slug)
    review = Review.objects.filter(product=product)
    seller = Seller.objects.get(user=request.user)

    # Calculate metrics for the dashboard
    # Total sales count (number of order items for this product)
    total_sales = OrderItem.objects.filter(product=product).count()

    # Calculate total quantity sold
    total_quantity_sold = OrderItem.objects.filter(product=product).aggregate(
        total_quantity=Sum('quantity')
    )['total_quantity'] or 0

    # Calculate revenue (quantity sold × product price)
    revenue = total_quantity_sold * product.price

    # Get weekly sales data (last 7 days)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=7)

    weekly_sales = []
    week_days = []

    for i in range(7):
        day = start_date + timedelta(days=i)
        day_sales = OrderItem.objects.filter(
            product=product,
            order__order_date__date=day.date()
        ).aggregate(day_total=Sum('quantity'))['day_total'] or 0
        weekly_sales.append(day_sales)
        week_days.append(day.strftime('%a'))  # Mon, Tue, etc.

    # Get return count (assuming returns are orders with status 'returned')
    # Since we don't have return status, we'll calculate based on some logic
    # For now, let's assume no returns or use a placeholder
    returns_count = 0

    # Calculate review statistics
    review_stats = {
        'total_reviews': review.count(),
        'average_rating': review.aggregate(Avg('rating'))['rating__avg'] or 0,
    }

    context = {
        'product': product,
        'review': review,
        'total_sales': total_sales,
        'total_quantity_sold': total_quantity_sold,
        'revenue': revenue,
        'weekly_sales': weekly_sales,
        'week_days': week_days,
        'returns_count': returns_count,
        'review_stats': review_stats,
        'seller':seller
    }

    return render(request, 'seller/product_details.html', context)
# def seller_profile(request):
#     seller=Seller.objects.get(user=request.user)
#     print(seller)
#     return render(request,'seller/seller_profile.html',{'seller':seller})
@login_required(login_url='seller/login')
@role_required("seller", login_url="/seller/login")
def seller_profile(request):
    # This logic is correct based on your snippet
    seller = Seller.objects.get(user=request.user)

    # We pass the PasswordChangeForm to the template
    password_form = PasswordChangeForm(request.user)

    context = {
        'seller': seller,
        'password_form': password_form,
    }
    return render(request, 'seller/seller_profile.html', context)
# In your Seller/Views.py
@login_required(login_url='seller/login')
@role_required("seller", login_url="/seller/login")
def seller_password_change(request):
    if request.method == 'POST':
        # Use Django's built-in PasswordChangeForm
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Important: updates the session with the new password hash
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            # Redirect to the profile page
            return redirect('profile_update')
        else:
            # Re-render the profile page with the error-filled form
            messages.error(request, 'Please correct the error below.')
            seller = Seller.objects.get(user=request.user)
            context = {
                'seller': seller,
                'password_form': form,
            }
            return render(request, 'seller/seller_profile.html', context)
    else:
        # Should only be accessed via POST from the form
        return redirect('seller_profile')


class SellerProfileForm:
    pass



@login_required(login_url='seller/login')
@role_required("seller", login_url="/seller/login")
def seller_profile_update(request):
    try:
        seller = Seller.objects.get(user=request.user)
    except Seller.DoesNotExist:
        messages.error(request, "Seller profile not found.")
        return redirect('seller_profile')

    if request.method == 'POST':
        # Pass the request.POST data, request.FILES for the image, and the instance
        form = SellerProfileForm(request.POST, request.FILES, instance=seller)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your shop details have been successfully updated!')
            return redirect('seller_profile')
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        # Initialize the form with the current seller data for a GET request
        form = SellerProfileForm(instance=seller)

    # Render the profile page again, passing the form context for the toggleable section
    # You might need to update your seller_profile.html to accept 'form' as a context variable
    return render(request, 'seller/seller_profile.html', {'seller': seller, 'profile_form': form})
def seller_forgott(request):
    return render(request,'seller/seller_forgott.html')
@login_required(login_url='/seller/login')
@role_required("seller", login_url="/seller/login")
def seller_logout(request):

    logout(request)
    return redirect('seller_login')
@login_required(login_url='seller/login')
@role_required("seller", login_url="/seller/login")
def seller_delete_profile(request):
    if request.method == 'POST':
        # Perform necessary checks (e.g., password confirmation if you added a field)

        try:
            seller = Seller.objects.get(user=request.user)
            user = request.user

            # Critical: Delete the Seller object and the associated User object
            seller.delete()
            # user.delete() # Deleting the User is crucial for full removal

            logout(request) # Log the user out immediately
            messages.success(request, 'Your account has been successfully deleted.')
            return redirect('seller_register') # Redirect to a safe page
        except Seller.DoesNotExist:
            messages.error(request, 'Profile not found.')
            return redirect('profile_update')

    # Redirect if accessed via GET accidentally
    return redirect('profile_update')




# Create your views here.

