from datetime import timedelta

from django.core.paginator import Paginator
from django.db.models import Count, Sum, Avg, Q
from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from Seller.models import Product, Seller
from User.models import Order, Review
from .models import User, Category, SubCategory  # custom user model import


def admin_login(request):

    if request.user.is_authenticated and request.user.role == "admin":
        return redirect("admin_dashboard")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(username=username, password=password)

        if user is None:
            messages.error(request, "Invalid username or password ❌")
            return redirect("admin_login")

        if user.role != "admin":
            messages.error(request, "You are not authorized as admin ❌")
            return redirect("admin_login")

        login(request, user)
        return redirect("admin_dashboard")

    return render(request, "admin/admin_login.html")


@login_required(login_url="admin_login")
def admin_dashboard(request):
    if request.user.role != "admin":
        logout(request)
        messages.error(request, "Unauthorized access ❌")
        return redirect("admin_login")
    total_users = User.objects.count()
    total_customers = User.objects.filter(role='customer').count()
    total_sellers = User.objects.filter(role='seller').count()

    total_orders = Order.objects.count()
    total_products = Product.objects.count()

    # Calculate revenue (sum of all order amounts)
    platform_revenue = Order.objects.aggregate(total_revenue=Sum('total_amount'))['total_revenue'] or 0

    # Order status counts
    pending_orders = Order.objects.filter(status='placed').count()
    processing_orders = Order.objects.filter(status='processing').count()
    shipped_orders = Order.objects.filter(status='shipped').count()
    delivered_orders = Order.objects.filter(status='delivered').count()

    # Active sellers (sellers with at least one product)
    active_sellers = Seller.objects.annotate(product_count=Count('products')).filter(product_count__gt=0).count()

    # Recent orders (last 10)
    recent_orders = Order.objects.select_related('user').order_by('-order_date')[:10]

    # Calculate stats for different time periods (for charts)
    today = timezone.now().date()

    # Last 7 days orders for weekly chart
    last_week = today - timedelta(days=7)
    weekly_orders = Order.objects.filter(
        order_date__date__gte=last_week
    ).values('order_date__date').annotate(
        count=Count('id'),
        revenue=Sum('total_amount')
    ).order_by('order_date__date')

    # Last 30 days for monthly chart
    last_month = today - timedelta(days=30)
    monthly_orders = Order.objects.filter(
        order_date__date__gte=last_month
    ).values('order_date__date').annotate(
        count=Count('id'),
        revenue=Sum('total_amount')
    ).order_by('order_date__date')

    # Last 12 months for yearly chart
    last_year = today - timedelta(days=365)
    yearly_orders = Order.objects.filter(
        order_date__date__gte=last_year
    ).values('order_date__month').annotate(
        count=Count('id'),
        revenue=Sum('total_amount')
    ).order_by('order_date__month')

    context = {
        'total_users': total_users,
        'total_customers': total_customers,
        'total_sellers': total_sellers,
        'total_orders': total_orders,
        'total_products': total_products,
        'platform_revenue': platform_revenue,
        'recent_orders': recent_orders,
        'pending_orders': pending_orders,
        'processing_orders': processing_orders,
        'shipped_orders': shipped_orders,
        'delivered_orders': delivered_orders,
        'active_sellers': active_sellers,
        'weekly_orders': list(weekly_orders),
        'monthly_orders': list(monthly_orders),
        'yearly_orders': list(yearly_orders),
    }

    return render(request, "admin/admin_dashboard.html", context)

@login_required(login_url="admin_login")
def admin_logout(request):
    logout(request)
    messages.success(request, "Logged out successfully 👋")
    return redirect("admin_login")




def create_temp_admin(request):
    try:
        User.objects.get(username="shopAdmin")
        return HttpResponse("Admin already exists ️")
    except User.DoesNotExist:
        User.objects.create_user(
            username="shopAdmin",
            password="admin123",
            contact="9876543210",
            role="admin"
        )
        return HttpResponse(
            "Admin created successfully 🎉<br>"
            "Username: shopAdmin<br>Password: admin123"
        )


@login_required(login_url="admin_login")
def user_management(request):
    if request.user.role != "admin":
        messages.error(request, "Unauthorized access ❌")
        return redirect("admin_login")

    users = User.objects.all().order_by('-created_at')
    customers = User.objects.filter(role='customer')
    sellers = User.objects.filter(role='seller')
    admins = User.objects.filter(role='admin')

    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(contact__icontains=search_query)
        )

    # Filter by role
    role_filter = request.GET.get('role', '')
    if role_filter:
        users = users.filter(role=role_filter)

    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        if status_filter == 'active':
            users = users.filter(is_active=True)
        elif status_filter == 'inactive':
            users = users.filter(is_active=False)

    # Get role choices from User model
    ROLE_CHOICES = User.ROLE_CHOICES

    context = {
        'users': users,
        'customers': customers,
        'sellers': sellers,
        'admins': admins,
        'search_query': search_query,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'ROLE_CHOICES': ROLE_CHOICES,
    }
    return render(request, "admin/admin_users.html", context)





@login_required(login_url="admin_login")
def product_management(request):
    if request.user.role != "admin":
        messages.error(request, "Unauthorized access ❌")
        return redirect("admin_login")

    try:
        # Get all products with related data
        products = Product.objects.select_related(
            'seller',
            'sub_category',
            'sub_category__category'
        ).prefetch_related('images', 'reviews').all().order_by('-id')

        # Get categories and subcategories for filters
        categories = Category.objects.all()
        subcategories = SubCategory.objects.all()
        sellers = Seller.objects.all()

        # Search functionality
        search_query = request.GET.get('search', '')
        if search_query:
            products = products.filter(
                Q(product_name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(seller__shop_name__icontains=search_query)
            )

        # Filter by category
        category_filter = request.GET.get('category', '')
        if category_filter:
            products = products.filter(sub_category__category_id=category_filter)

        # Filter by subcategory
        subcategory_filter = request.GET.get('subcategory', '')
        if subcategory_filter:
            products = products.filter(sub_category_id=subcategory_filter)

        # Filter by seller
        seller_filter = request.GET.get('seller', '')
        if seller_filter:
            products = products.filter(seller_id=seller_filter)

        # Filter by stock status
        stock_filter = request.GET.get('stock', '')
        if stock_filter:
            if stock_filter == 'in_stock':
                products = products.filter(stock__gt=0)
            elif stock_filter == 'out_of_stock':
                products = products.filter(stock=0)
            elif stock_filter == 'low_stock':
                products = products.filter(stock__lte=10, stock__gt=0)

        # Filter by rating
        rating_filter = request.GET.get('rating', '')
        if rating_filter:
            products = products.filter(rating__gte=float(rating_filter))

        # Calculate stats
        total_products = products.count()
        out_of_stock = products.filter(stock=0).count()
        low_stock = products.filter(stock__lte=10, stock__gt=0).count()
        high_rated = products.filter(rating__gte=4.0).count()

        # Pagination
        paginator = Paginator(products, 10)  # Show 10 products per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'products': page_obj,
            'categories': categories,
            'subcategories': subcategories,
            'sellers': sellers,
            'search_query': search_query,
            'category_filter': category_filter,
            'subcategory_filter': subcategory_filter,
            'seller_filter': seller_filter,
            'stock_filter': stock_filter,
            'rating_filter': rating_filter,
            'total_products': total_products,
            'out_of_stock': out_of_stock,
            'low_stock': low_stock,
            'high_rated': high_rated,
        }

        return render(request, "admin/admin_products.html", context)

    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('admin_dashboard')


def order_management(request):
    if request.user.role != "admin":
        messages.error(request, "Unauthorized access ❌")
        return redirect("admin_login")

    try:
        # Get all orders with related data
        orders = Order.objects.select_related('user').prefetch_related(
            'order_items',
            'order_items__product'
        ).all().order_by('-order_date')

        # Search functionality
        search_query = request.GET.get('search', '')
        if search_query:
            orders = orders.filter(
                Q(id__icontains=search_query) |
                Q(user__username__icontains=search_query) |
                Q(user__email__icontains=search_query) |
                Q(shipping_address__icontains=search_query)
            )

        # Filter by status
        status_filter = request.GET.get('status', '')
        if status_filter:
            orders = orders.filter(status=status_filter)

        # Filter by date
        date_filter = request.GET.get('date', '')
        if date_filter:
            if date_filter == 'today':
                today = timezone.now().date()
                orders = orders.filter(order_date__date=today)
            elif date_filter == 'week':
                week_ago = timezone.now().date() - timedelta(days=7)
                orders = orders.filter(order_date__date__gte=week_ago)
            elif date_filter == 'month':
                month_ago = timezone.now().date() - timedelta(days=30)
                orders = orders.filter(order_date__date__gte=month_ago)

        # Calculate stats
        total_orders = orders.count()
        total_revenue = orders.aggregate(total=Sum('total_amount'))['total'] or 0
        pending_orders = orders.filter(status='placed').count()
        delivered_orders = orders.filter(status='delivered').count()

        # Status counts for stats - using direct counts instead of dictionary
        placed_orders = orders.filter(status='placed').count()
        processing_orders = orders.filter(status='processing').count()
        shipped_orders = orders.filter(status='shipped').count()
        delivered_orders_count = orders.filter(status='delivered').count()

        # Recent orders (for quick stats)
        recent_orders = orders[:5]

        # Pagination
        paginator = Paginator(orders, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'orders': page_obj,
            'search_query': search_query,
            'status_filter': status_filter,
            'date_filter': date_filter,
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'pending_orders': pending_orders,
            'delivered_orders': delivered_orders,
            'placed_orders': placed_orders,
            'processing_orders': processing_orders,
            'shipped_orders': shipped_orders,
            'delivered_orders_count': delivered_orders_count,
            'recent_orders': recent_orders,
            'STATUS_CHOICES': Order.STATUS_CHOICES,
        }

        return render(request, "admin/admin_orders.html", context)

    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('admin_dashboard')


@login_required(login_url="admin_login")
def order_detail(request, order_id):
    if request.user.role != "admin":
        messages.error(request, "Unauthorized access ❌")
        return redirect("admin_login")

    order = get_object_or_404(Order, id=order_id)
    order_items = order.order_items.select_related('product').all()

    context = {
        'order': order,
        'order_items': order_items,
    }

    return render(request, "admin/admin_order_detail.html", context)


@login_required(login_url="admin_login")
def seller_management(request):
    if request.user.role != "admin":
        messages.error(request, "Unauthorized access ❌")
        return redirect("admin_login")

    try:
        # Get all sellers with related data
        sellers = Seller.objects.select_related('user').prefetch_related('products').all()

        # Calculate product counts and total sales for each seller
        sellers = sellers.annotate(
            product_count=Count('products'),
            total_sales=Sum('products__price')  # This is simplified - you might want to use actual order data
        )

        # Search functionality
        search_query = request.GET.get('search', '')
        if search_query:
            sellers = sellers.filter(
                Q(shop_name__icontains=search_query) |
                Q(user__username__icontains=search_query) |
                Q(user__email__icontains=search_query) |
                Q(address__icontains=search_query)
            )

        # Filter by status
        status_filter = request.GET.get('status', '')
        if status_filter == 'active':
            sellers = sellers.filter(user__is_active=True)
        elif status_filter == 'inactive':
            sellers = sellers.filter(user__is_active=False)

        # Calculate stats
        total_sellers = sellers.count()
        active_sellers = sellers.filter(user__is_active=True).count()
        total_products = sum(seller.product_count for seller in sellers)
        verified_sellers = sellers.filter(website__isnull=False).count()  # Using website as verification proxy

        # Recent sellers (for quick stats)
        recent_sellers = sellers.order_by('-user__date_joined')[:5]

        # Pagination
        paginator = Paginator(sellers, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'sellers': page_obj,
            'search_query': search_query,
            'status_filter': status_filter,
            'total_sellers': total_sellers,
            'active_sellers': active_sellers,
            'total_products': total_products,
            'verified_sellers': verified_sellers,
            'recent_sellers': recent_sellers,
        }

        return render(request, "admin/admin_sellers.html", context)

    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('admin_dashboard')


@login_required(login_url="admin_login")
def toggle_seller_status(request, seller_id):
    if request.user.role != "admin":
        messages.error(request, "Unauthorized access ❌")
        return redirect("admin_login")

    seller = get_object_or_404(Seller, id=seller_id)
    seller.user.is_active = not seller.user.is_active
    seller.user.save()

    action = "activated" if seller.user.is_active else "deactivated"
    messages.success(request, f"Seller {seller.shop_name} has been {action} successfully.")
    return redirect('seller_management')

@login_required(login_url="admin_login")
def analytics(request):
    if request.user.role != "admin":
        messages.error(request, "Unauthorized access ❌")
        return redirect("admin_login")

    # Sales analytics
    total_sales = Order.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    avg_order_value = Order.objects.aggregate(avg=Avg('total_amount'))['avg'] or 0

    # Top selling products
    top_products = Product.objects.annotate(
        order_count=Count('order_items')
    ).order_by('-order_count')[:10]

    # Customer analytics
    top_customers = User.objects.filter(role='customer').annotate(
        order_count=Count('orders'),
        total_spent=Sum('orders__total_amount')
    ).order_by('-total_spent')[:10]

    context = {
        'total_sales': total_sales,
        'avg_order_value': avg_order_value,
        'top_products': top_products,
        'top_customers': top_customers,
    }
    return render(request, "admin/admin_analytics.html", context)


@login_required(login_url="admin_login")
def admin_settings(request):
    if request.user.role != "admin":
        messages.error(request, "Unauthorized access ❌")
        return redirect("admin_login")

    return render(request, "admin/admin_settings.html")


# Additional utility views
@login_required(login_url="admin_login")
def toggle_user_status(request, user_id):
    if request.user.role != "admin":
        messages.error(request, "Unauthorized access ❌")
        return redirect("admin_login")

    user = get_object_or_404(User, id=user_id)
    user.is_active = not user.is_active
    user.save()

    action = "activated" if user.is_active else "deactivated"
    messages.success(request, f"User {user.username} has been {action} successfully.")
    return redirect('user_management')


@login_required(login_url="admin_login")
def update_order_status(request, order_id):
    if request.user.role != "admin":
        messages.error(request, "Unauthorized access ❌")
        return redirect("admin_login")

    if request.method == "POST":
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')

        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            messages.success(request, f"Order #{order.id} status updated to {new_status}.")
        else:
            messages.error(request, "Invalid status selected.")

    return redirect('order_management')




@login_required(login_url="admin_login")
def update_user_role(request, user_id):
    if request.user.role != "admin":
        messages.error(request, "Unauthorized access ❌")
        return redirect("admin_login")

    if request.method == "POST":
        user = get_object_or_404(User, id=user_id)
        new_role = request.POST.get('role')

        # Prevent admin from changing their own role
        if user == request.user:
            messages.error(request, "You cannot change your own role ❌")
            return redirect('user_management')

        if new_role in dict(User.ROLE_CHOICES):
            user.role = new_role
            user.save()
            messages.success(request, f"User {user.username} role updated to {new_role}.")
        else:
            messages.error(request, "Invalid role selected.")

    return redirect('user_management')


@login_required(login_url="admin_login")
def delete_user(request, user_id):
    if request.user.role != "admin":
        messages.error(request, "Unauthorized access ❌")
        return redirect("admin_login")

    user = get_object_or_404(User, id=user_id)

    # Prevent admin from deleting themselves
    if user == request.user:
        messages.error(request, "You cannot delete your own account ❌")
        return redirect('user_management')


def toggle_product_status(request, product_id):
    if request.user.role != "admin":
        messages.error(request, "Unauthorized access ❌")
        return redirect("admin_login")

    product = get_object_or_404(Product, id=product_id)

    # Toggle product status (you might want to add an 'is_active' field to Product model)
    # For now, we'll toggle stock between 0 and a default value
    if product.stock > 0:
        product.stock = 0
        action = "out of stock"
    else:
        product.stock = 10  # Default stock value
        action = "in stock"

    product.save()
    messages.success(request, f"Product '{product.product_name}' marked as {action}.")
    return redirect('product_management')


@login_required(login_url="admin_login")
def review_management(request):
    if request.user.role != "admin":
        messages.error(request, "Unauthorized access ❌")
        return redirect("admin_login")

    try:
        # Get all reviews with related data
        reviews = Review.objects.select_related('user', 'product').all().order_by('-created_at')

        # Search functionality
        search_query = request.GET.get('search', '')
        if search_query:
            reviews = reviews.filter(
                Q(user__username__icontains=search_query) |
                Q(product__name__icontains=search_query) |
                Q(comment__icontains=search_query)
            )

        # Filter by rating
        rating_filter = request.GET.get('rating', '')
        if rating_filter:
            reviews = reviews.filter(rating=rating_filter)

        # Filter by date
        date_filter = request.GET.get('date', '')
        if date_filter:
            if date_filter == 'today':
                today = timezone.now().date()
                reviews = reviews.filter(created_at__date=today)
            elif date_filter == 'week':
                week_ago = timezone.now().date() - timedelta(days=7)
                reviews = reviews.filter(created_at__date__gte=week_ago)
            elif date_filter == 'month':
                month_ago = timezone.now().date() - timedelta(days=30)
                reviews = reviews.filter(created_at__date__gte=month_ago)

        # Calculate stats
        total_reviews = reviews.count()
        average_rating = reviews.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0

        # Rating distribution
        rating_distribution = reviews.values('rating').annotate(count=Count('id')).order_by('rating')

        # Recent reviews
        recent_reviews = reviews[:5]

        # Pagination
        paginator = Paginator(reviews, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'reviews': page_obj,
            'search_query': search_query,
            'rating_filter': rating_filter,
            'date_filter': date_filter,
            'total_reviews': total_reviews,
            'average_rating': round(average_rating, 1),
            'rating_distribution': rating_distribution,
            'recent_reviews': recent_reviews,
        }

        return render(request, "admin/admin_reviews.html", context)

    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('admin_dashboard')


@login_required(login_url="admin_login")
def review_detail(request, review_id):
    if request.user.role != "admin":
        messages.error(request, "Unauthorized access ❌")
        return redirect("admin_login")

    review = get_object_or_404(Review, id=review_id)

    context = {
        'review': review,
    }

    return render(request, "admin/admin_review_detail.html", context)


@login_required(login_url="admin_login")
def delete_review(request, review_id):
    if request.user.role != "admin":
        messages.error(request, "Unauthorized access ❌")
        return redirect("admin_login")

    if request.method == "POST":
        review = get_object_or_404(Review, id=review_id)
        review.delete()
        messages.success(request, "Review deleted successfully ✅")
        return redirect('review_management')

    return redirect('review_detail', review_id=review_id)