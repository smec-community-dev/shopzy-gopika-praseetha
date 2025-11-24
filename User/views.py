import re

import razorpay
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages as dj_messages
from django.views.decorators.csrf import csrf_exempt
from unicodedata import category

from Core.models import User,Category,SubCategory
from Seller.models import Product
from decorators.decorators import role_required
from django.conf import settings
from .models import Customer,Review,ReviewImage,Wishlist,Cart,Order,OrderItem,Address
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required

# Create your views here.

def user_register(request):
    if request.method == "POST":

        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        contact = request.POST.get('contact')
        address = request.POST.get('address')
        profile_img = request.FILES.get('profile_img')

        errors = {}

        if password != confirm_password:
            errors['confirm_password'] = "Passwords do not match"

        if len(password) < 8:
            errors['password'] = "Password must be at least 8 characters long"

        if User.objects.filter(username=username).exists():
            errors['username'] = "Username already taken"

        if User.objects.filter(email=email).exists():
            errors['email'] = "Email already registered"
        else:
            try:
                validate_email(email)
            except ValidationError:
                errors['email'] = "Invalid email address"

        phone_pattern = r'^\d{10}$'
        if not re.match(phone_pattern, contact):
            errors['contact'] = "Phone number must be 10 digits"
        elif Customer.objects.filter(user__contact=contact).exists():
            errors['contact'] = "Phone number already registered"

        if errors:
            return render(request, 'user/user_register.html', {
                "errors": errors,
                "form_data": request.POST  # to refill input fields
            })

        user = User(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            contact=contact,

        )
        user.set_password(password)
        user.save()

        custom_user = Customer(
            user=user,
            address=address,
            profile_img=profile_img
        )
        custom_user.save()

        dj_messages.success(request, "Registration successful! You can login now.")
        return redirect('user_login')

    return render(request, 'user/user_register.html')

def user_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.role == "customer":
                login(request, user)
                return redirect('/')
            else:
                return render(request, 'user/user_login.html', {'error': 'Access denied! Only customers can login here.'})
        else:
            return render(request, 'user/user_login.html', {'error': 'Invalid username or password'})
    return render(request, 'user/user_login.html')

def home(request):
    products = Product.objects.all()[:4]
    categories = Category.objects.all()

    if request.user.is_authenticated:

        for p in products:
            # Cart check using .filter().exists()
            # p.cart_exists = Cart.objects.filter(user=request.user, product=p).exists()

            cart_item = Cart.objects.filter(user=request.user, product=p).first()
            p.carted = bool(cart_item)
            p.cart_item_id = cart_item.id if cart_item else None
            # Wishlist check using .filter().exists()
            p.wishlist_exists = Wishlist.objects.filter(user=request.user, product=p).exists()

    else:
        for p in products:
            # p.cart_exists = False
            p.carted = False
            p.cart_item_id = None
            p.wishlist_exists = False
    query = request.GET.get('q', '')
    products = Product.objects.all()



    return render(request,'user/home.html',{"products": products,"categories": categories,})

def user_single_product(request, slug):
    try:
        product = Product.objects.get(slug=slug)
    except Product.DoesNotExist:
        return redirect("/")

    images = product.images.all()

    if request.user.is_authenticated:
        wishlisted = Wishlist.objects.filter(user=request.user, product=product).exists()
    else:
        wishlisted = False

    carted = False
    cart_item_id = None

    if request.user.is_authenticated:
        cart_item = Cart.objects.filter(user=request.user, product=product).first()
        if cart_item:
            carted = True
            cart_item_id = cart_item.id
    reviews = Review.objects.filter(product=product).order_by('-created_at')

    return render(request, "user/user_single_product.html", {
        "product": product,
        "images": images,
        "wishlisted": wishlisted,
        "carted": carted,
        "cart_item_id": cart_item_id,
        "reviews":reviews
    })

@role_required("customer", login_url="/user_login")
def user_add_wishlist(request, slug):
    try:
        product = Product.objects.get(slug=slug)
    except Product.DoesNotExist:
        return redirect("/shop")

    try:
        existing = Wishlist.objects.get(user=request.user, product=product)
        existing.delete()
    except Wishlist.DoesNotExist:
        Wishlist.objects.create(user=request.user, product=product)

    return redirect(request.META.get("HTTP_REFERER", request.path))


@role_required("customer", login_url="/user_login")
def user_view_wishlist(request):
    items = Wishlist.objects.filter(user=request.user).select_related("product")
    return render(request, "user/user_wishlist.html", {"data": items})


@role_required("customer", login_url="/user_login")
def user_remove_wishlist(request, id):
    """Remove wishlist item"""
    try:
        item = Wishlist.objects.get(id=id, user=request.user)
        item.delete()
    except Wishlist.DoesNotExist:
        pass

    return redirect('user_view_wishlist')

@role_required("customer", login_url="/user_login")
def user_logout(request):
    logout(request)
    return redirect('/')

@role_required("customer", login_url="/user_login")
def user_add_to_cart(request, slug):
    try:
        product = Product.objects.get(slug=slug)
    except Product.DoesNotExist:
        return redirect(request.path)

    qty = request.GET.get("qty") or request.POST.get("quantity") or 1
    try:
        qty = int(qty)
        if qty < 1:
            qty = 1
    except:
        qty = 1

    # Stock check
    if product.stock <= 0:
        dj_messages.error(request, "Sorry, this product is out of stock.")
        return redirect(request.path)

    cart_item, created = Cart.objects.get_or_create(
        user=request.user,
        product=product,
        defaults={"quantity": qty}
    )

    if not created:
        new_qty = cart_item.quantity + qty
        if new_qty > product.stock:
            new_qty = product.stock
            dj_messages.info(request, f"Only {product.stock} in stock. Quantity adjusted.")

        cart_item.quantity = new_qty
        cart_item.save()
    else:
        if qty > product.stock:
            qty = product.stock
            cart_item.quantity = qty
            cart_item.save()
            dj_messages.info(request, f"Only {product.stock} in stock. Quantity adjusted.")

    return redirect(request.META.get("HTTP_REFERER", "/shop/"))


@role_required("customer", login_url="/user_login")
def user_view_cart(request):
    items = Cart.objects.filter(user=request.user).select_related("product")
    for item in items:
        item.subtotal = item.product.price * item.quantity
    total = sum(item.subtotal for item in items)
    return render(request,'user/user_view_cart.html',{'items': items,'total': total})


@role_required("customer", login_url="/user_login")
def user_remove_from_cart(request, id):
    try:
        item = Cart.objects.get(id=id, user=request.user)
        item.delete()
    except Cart.DoesNotExist:
        pass

    return redirect(request.META.get("HTTP_REFERER", "/user_view_cart"))


@role_required("customer", login_url="/user_login")
def user_update_cart(request, id):

    if request.method != "POST":
        return redirect('user_view_cart')

    try:
        cart_item = Cart.objects.get(id=id, user=request.user)
    except Cart.DoesNotExist:
        dj_messages.error(request, "Cart item not found.")
        return redirect('user_view_cart')

    qty = request.POST.get("quantity", 1)

    try:
        qty = int(qty)
        if qty < 1:
            qty = 1
    except:
        qty = 1

    stock = cart_item.product.stock
    if qty > stock:
        qty = stock
        dj_messages.info(request, f"Only {stock} in stock. Quantity adjusted.")

    cart_item.quantity = qty
    cart_item.save()

    dj_messages.success(request, "Cart updated.")
    return redirect('user_view_cart')

@role_required("customer", login_url="/user_login")
def user_checkout(request):
    items = Cart.objects.filter(user=request.user).select_related("product")
    addresses = Address.objects.filter(user=request.user)  # <-- new
    for item in items:
        item.subtotal = item.product.price * item.quantity
    total = sum(item.subtotal for item in items)

    return render(request, "user/user_checkout.html", {"items": items,"total": total,"addresses": addresses})


@role_required("customer", login_url="/user_login")
def user_update_checkout_quantity(request, id):

    if request.method != "POST":
        return redirect("user_checkout")
    try:
        cart_item = Cart.objects.get(id=id, user=request.user)
    except Cart.DoesNotExist:
        dj_messages.error(request, "Item not found.")
        return redirect("user_checkout")
    qty = request.POST.get("quantity", 1)
    try:
        qty = int(qty)
        if qty < 1:
            qty = 1
    except:
        qty = 1
    stock = cart_item.product.stock
    if qty > stock:
        qty = stock
        dj_messages.info(request, f"Only {stock} available.")

    cart_item.quantity = qty
    cart_item.save()

    dj_messages.success(request, "Updated successfully!")
    return redirect("user_checkout")


@role_required("customer", login_url="/user_login")
def place_order(request):
    if request.method != "POST":
        return redirect("user_checkout")

    user = request.user
    buy_now = request.session.get("buy_now")

    items = []

    if buy_now:
        product = Product.objects.filter(slug=buy_now.get("slug")).first()
        if not product:
            dj_messages.error(request, "Product not found.")
            request.session.pop("buy_now", None)
            return redirect("home")

        qty = min(int(buy_now.get("qty", 1)), product.stock)
        items.append({"product": product, "quantity": qty})

    else:
        cart_items = Cart.objects.filter(user=user).select_related("product")
        if not cart_items.exists():
            dj_messages.error(request, "Cart is empty.")
            return redirect("user_view_cart")

        for c in cart_items:
            if c.quantity > c.product.stock:
                dj_messages.error(request, f"Only {c.product.stock} left for {c.product.product_name}.")
                return redirect("user_checkout")
            items.append({"product": c.product, "quantity": c.quantity})

    addr_id = request.POST.get("selected_address")
    if addr_id:
        addr = get_object_or_404(Address, id=addr_id, user=user)
    else:
        fn = request.POST.get("full_name")
        ph = request.POST.get("phone")
        a1 = request.POST.get("address_line1")
        a2 = request.POST.get("address_line2") or None
        ct = request.POST.get("city")
        st = request.POST.get("state")
        pc = request.POST.get("pincode")
        co = request.POST.get("country", "India")

        if not (fn and ph and a1 and ct and st and pc):
            dj_messages.error(request, "Please fill all required fields.")
            return redirect("user_checkout")

        addr = Address.objects.create(
            user=user, full_name=fn, phone=ph, address_line1=a1,
            address_line2=a2, city=ct, state=st, pincode=pc, country=co
        )

    final_address = (
        f"{addr.full_name}, {addr.phone}, {addr.address_line1}, "
        f"{(addr.address_line2+', ') if addr.address_line2 else ''}"
        f"{addr.city}, {addr.state} - {addr.pincode}, {addr.country}"
    )

    total = sum(i["product"].price * i["quantity"] for i in items)

    order = Order(
        user=user,
        total_amount=total,
        shipping_address=final_address,
        status="processing"
    )
    order.save()

    # Prevent second save from inserting again
    if not order.slug:
        generated_slug = f"order-{order.id}"
        Order.objects.filter(id=order.id).update(slug=generated_slug)
        order.slug = generated_slug

    for i in items:
        OrderItem.objects.create(order=order, product=i["product"], quantity=i["quantity"])
        i["product"].stock -= i["quantity"]
        i["product"].save()

    if buy_now:
        request.session.pop("buy_now", None)
    else:
        Cart.objects.filter(user=user).delete()

    dj_messages.success(request, "Order placed successfully!")
    return redirect("order_success", order_slug=order.slug)


@login_required(login_url='/user_login')
def user_dashboard(request):
    return render(request, 'user/user_dashboard.html')

@role_required("customer", login_url="/user_login")
def user_orders(request):
    orders = Order.objects.filter(user=request.user).prefetch_related("order_items__product")
    for order in orders:
        for item in order.order_items.all():
            item.subtotal = item.quantity * item.product.price
    return render(request, "user/orders_table.html", {"orders": orders})

def add_review(request, slug):
    try:
        product = Product.objects.get(slug=slug)
    except Product.DoesNotExist:
        dj_messages.error(request, "Product not found.")
        return redirect("user_orders", slug="all")
    order = Order.objects.filter(order_items__product=product, user=request.user).first()
    if not order:
        dj_messages.error(request, "You can only review purchased products.")
        return redirect("user_orders", slug="all")

    if request.method == "POST":
        review_text = request.POST.get("review")
        rating = request.POST.get("rating")

        review = Review.objects.create(user=request.user,product=product,review=review_text,rating=rating)

        for img in request.FILES.getlist("images"):
            ReviewImage.objects.create(review=review, review_img=img)
        dj_messages.success(request, "Review added successfully!")

        return redirect("user_orders")

    return render(request, "user/add_review.html", {"product": product,"order_slug": order.slug})

def shop_page(request):

    products_qs = Product.objects.all().prefetch_related("images")

    query = request.GET.get('q', '')

    # products = Product.objects.all()

    if query:
        products_qs = products_qs.filter(
            Q(product_name__icontains=query) |
            Q(description__icontains=query) |
            Q(price__icontains=query) |
            Q(sub_category__sub_category_name__icontains=query) |
            Q(sub_category__category__category_name__icontains=query) |
            Q(seller__shop_name__icontains=query)
        )

    selected_category = request.GET.get("category")
    if selected_category:
        products_qs = products_qs.filter(sub_category__category__slug=selected_category)

    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")

    if min_price:
        products_qs = products_qs.filter(price__gte=min_price)

    if max_price:
        products_qs = products_qs.filter(price__lte=max_price)

    sort_option = request.GET.get("sort")

    if sort_option == "low-high":
        products_qs = products_qs.order_by("price")

    elif sort_option == "high-low":
        products_qs = products_qs.order_by("-price")

    elif sort_option == "rating":
        products_qs = products_qs.order_by("-avg_rating")

    elif sort_option == "new":
        products_qs = products_qs.order_by("-created_at")

    # PAGINATION
    paginator = Paginator(products_qs, 9)
    page_number = request.GET.get("page")
    products = paginator.get_page(page_number)

    # CART + WISHLIST FLAGS
    if request.user.is_authenticated:
        for p in products:
            cart_item = Cart.objects.filter(user=request.user, product=p).first()
            p.carted = bool(cart_item)
            p.cart_item_id = cart_item.id if cart_item else None
            p.wishlist_exists = Wishlist.objects.filter(user=request.user, product=p).exists()
    else:
        for p in products:
            p.carted = False
            p.cart_item_id = None
            p.wishlist_exists = False

    if request.user.is_authenticated:
        wishlist_items = list(
            Wishlist.objects.filter(user=request.user).values_list("product_id", flat=True)
        )
        wishlist_items = [int(x) for x in wishlist_items]
    else:
        wishlist_items = []

    return render(request, "user/shop.html", {
        "products": products,
        "categories": Category.objects.all(),
        "sub_categories": SubCategory.objects.all(),
        "query": query,
        "selected_category": selected_category,
        "sort_option": sort_option,      # <-- IMPORTANT
        "wishlist_items": wishlist_items,
    })
@role_required("customer", login_url="/user_login")
def cancel_order(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        dj_messages.error(request, "Order not found.")
        return redirect("user_orders")

    # Only cancel if placed or processing
    if order.status not in ["placed", "processing"]:
        dj_messages.error(request, "This order cannot be cancelled.")
        return redirect("user_orders")

    # Restore stock
    for item in order.order_items.all():
        product = item.product
        product.stock += item.quantity
        product.save()

    # Update status
    order.status = "cancelled"
    order.save()

    dj_messages.success(request, "Order cancelled successfully.")
    return redirect("user_orders")

@login_required(login_url='/user_login')
def user_dashboard(request):
    user = request.user

    try:
        profile = Customer.objects.get(user=user)
    except Customer.DoesNotExist:
        profile = None

    total_orders = Order.objects.filter(user=user).count()
    pending_orders = Order.objects.filter(user=user, status="placed").count()
    total_addresses = Address.objects.filter(user=user).count()

    addresses = Address.objects.filter(user=user).order_by('-is_default', 'id')


    context = {
        "user": user,
        "profile": profile,
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "total_addresses": total_addresses,
        "addresses": addresses,
    }

    return render(request, "user/user_dashboard.html", context)



@login_required(login_url='/user_login')
def user_profile_edit(request):
    user = request.user

    profile, created = Customer.objects.get_or_create(user=user)

    if request.method == "POST":
        # Update USER model fields
        user.first_name = request.POST.get("first_name")
        user.last_name = request.POST.get("last_name")
        user.email = request.POST.get("email")
        user.contact = request.POST.get("contact")
        user.address=request.POST.get("address")
        user.save()

        # Update PROFILE (Customer model)
        if request.FILES.get("profile_img"):
            profile.profile_img = request.FILES.get("profile_img")

        profile.save()

        return redirect("user_dashboard")

    return redirect("user_dashboard")

@role_required("customer", login_url="/user_login")
def user_checkout(request):
    user = request.user
    addresses = Address.objects.filter(user=user)

    buy_now = request.session.get("buy_now")
    items = []
    total = 0


    if buy_now:
        product = Product.objects.filter(slug=buy_now.get("slug")).first()

        if not product:
            request.session.pop("buy_now", None)
            dj_messages.error(request, "Product no longer available.")
            return redirect("home")

        qty = int(buy_now.get("qty", 1))
        qty = max(1, qty)
        qty = min(qty, product.stock)

        buy_now["qty"] = qty
        request.session["buy_now"] = buy_now

        class TempItem:
            pass

        temp = TempItem()
        temp.product = product
        temp.quantity = qty
        temp.subtotal = product.price * qty

        items = [temp]
        total = temp.subtotal

    else:

        cart_items = Cart.objects.filter(user=user).select_related("product")

        if not cart_items.exists():
            dj_messages.error(request, "Your cart is empty.")
            return redirect("user_view_cart")

        for it in cart_items:
            it.subtotal = it.product.price * it.quantity

        items = list(cart_items)
        total = sum(i.subtotal for i in items)

    return render(request, "user/user_checkout.html", {
        "items": items,
        "total": total,
        "addresses": addresses
    })


@role_required("customer", login_url="/user_login")
def user_buy_now(request, slug):
    if request.method != "POST":
        return redirect("user_single_product", slug=slug)

    product = get_object_or_404(Product, slug=slug)

    try:
        qty = int(request.POST.get("quantity", 1))
    except:
        qty = 1

    qty = max(1, qty)
    qty = min(qty, product.stock)

    request.session["buy_now"] = {
        "slug": product.slug,
        "qty": qty
    }

    request.session.set_expiry(20 * 60)

    return redirect("user_checkout")

@role_required("customer", login_url="/user_login")
def order_success(request, order_slug):
    order = get_object_or_404(Order, slug=order_slug, user=request.user)
    return render(request, "user/order_success.html", {"order": order})

@role_required("customer", login_url="/user_login")
def save_address(request):
    if request.method == "POST":

        user = request.user

        address_id = request.POST.get("address_id")

        if address_id:
            address = get_object_or_404(Address, id=address_id, user=user)
        else:
            address = Address(user=user)

        address.full_name = request.POST.get("name")
        address.phone = request.POST.get("phone")
        address.address_line1 = request.POST.get("address_line1")
        address.address_line2 = request.POST.get("address_line2")
        address.city = request.POST.get("city")
        address.state = request.POST.get("state")
        address.pincode = request.POST.get("zip")
        address.country = request.POST.get("country")

        is_default = request.POST.get("is_default") == "on"

        if is_default:
            Address.objects.filter(user=user, is_default=True).update(is_default=False)
            address.is_default = True
        else:
            if not Address.objects.filter(user=user, is_default=True).exists():
                address.is_default = True
            else:
                address.is_default = False

        address.save()

        return redirect("/user_dashboard/?section=addresses")

    return redirect("/user_dashboard")

@login_required
def delete_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    address.delete()

    remaining = Address.objects.filter(user=request.user)
    if remaining.exists() and not remaining.filter(is_default=True).exists():
        first = remaining.first()
        first.is_default = True
        first.save()

    return redirect("/user_dashboard/?section=addresses")

@login_required
def set_default_address(request, address_id):
    user = request.user

    Address.objects.filter(user=user, is_default=True).update(is_default=False)

    address = get_object_or_404(Address, id=address_id, user=user)
    address.is_default = True
    address.save()

    return redirect("/user_dashboard/?section=addresses")

@login_required(login_url='/user_login')
def change_password_view(request):
    if request.method == 'POST':
        user = request.user
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            return redirect('/user_dashboard?section=security')

        if len(new_password) < 8:
            return redirect('/user_dashboard?section=security')

        try:
            user.set_password(new_password)
            user.save()

            update_session_auth_hash(request, user)

            return redirect('/user_dashboard?section=security')

        except Exception as e:
            return redirect('/user_dashboard?section=security')

    return redirect('/user_dashboard?section=security')

def user_about(request):
    return render(request,'user/user_about.html')

def contact(request):
    return render(request, 'user/contact.html')

@csrf_exempt
def create_razorpay_order(request):
    if request.method == "POST":
        amount = request.POST.get("amount")

        amount_in_paise = int(float(amount) * 100)  # ₹ → paise

        client = razorpay.Client(auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        ))

        order = client.order.create({
            "amount": amount_in_paise,
            "currency": "INR",
            "payment_capture": 1
        })

    return JsonResponse({
            "order_id": order["id"],
            "key": settings.RAZORPAY_KEY_ID,
            "amount": amount_in_paise,
        })
