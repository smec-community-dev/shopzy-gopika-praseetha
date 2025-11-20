from django.shortcuts import render,redirect
from django.contrib import messages as dj_messages
from Core.models import User,Category,SubCategory
from Seller.models import Product
from decorators.decorators import role_required
from .models import Customer,Review,ReviewImage,Wishlist,Cart,Order,OrderItem,Address
from django.contrib.auth import authenticate,login,logout
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required

# Create your views here.

def user_register(request):
    if request.method == "POST":
        user = User()
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        user.password = request.POST.get('password')
        user.set_password(request.POST.get('password'))
        user.contact = request.POST.get('contact')
        user.role = "customer"
        user.save()
        custom_user=Customer()
        custom_user.user = user
        custom_user.address=request.POST.get('address')
        custom_user.profile_img = request.FILES.get('profile_img')
        custom_user.save()

    return render(request,'user/user_register.html')

def user_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.role == "customer":
                login(request, user)
                return redirect('/user_home')
            else:
                return render(request, 'user/user_login.html', {'error': 'Access denied! Only customers can login here.'})
        else:
            return render(request, 'user/user_login.html', {'error': 'Invalid username or password'})
    return render(request, 'user/user_login.html')


def user_home(request):
    q = request.GET.get("q", "")
    data = Product.objects.all()

    if q:
        data = data.filter(
            Q(product_name__icontains=q) |
            Q(sub_category__sub_category_name__icontains=q) |
            Q(sub_category__category__category_name__icontains=q)
        )

    paginator = Paginator(data, 8)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "user/user_home.html", {"data": page_obj,"page_obj": page_obj,"q": q})

def user_single_product(request, slug):
    try:
        product = Product.objects.get(slug=slug)
    except Product.DoesNotExist:
        return redirect("/user_home")
    images = product.images.all()
    if request.user.is_authenticated:
        carted=Cart.objects.filter(user=request.user,product=product).exists()
        wishlisted = Wishlist.objects.filter(user=request.user, product=product).exists()
    else:
        wishlisted = False
        carted=False
    return render(request, 'user/user_single_product.html', {'product': product,'images': images,'wishlisted': wishlisted,"carted":carted})


@role_required("customer", login_url="/user_login")
def user_add_wishlist(request, slug):
    try:
        product = Product.objects.get(slug=slug)
    except Product.DoesNotExist:
        return redirect("/user_home")
    try:
        data = Wishlist.objects.get(user=request.user, product=product)
        data.delete()
    except Wishlist.DoesNotExist:
        Wishlist.objects.create(user=request.user, product=product)
    return redirect('user_single_product', slug=slug)

@role_required("customer", login_url="/user_login")
def user_view_wishlist(request):
    data = Wishlist.objects.filter(user=request.user)
    return render(request, 'user/user_wishlist.html', {'data': data})

@role_required("customer", login_url="/user_login")
def user_remove_wishlist(request, id):
    data = Wishlist.objects.get(id=id)
    data.delete()
    return redirect('user_view_wishlist')

@role_required("customer", login_url="/user_login")
def user_logout(request):
    logout(request)
    return redirect('/user_home')

@role_required("customer", login_url="/user_login")
def user_add_to_cart(request, slug):
    try:
        product = Product.objects.get(slug=slug)
    except Product.DoesNotExist:
        return redirect("/user_home")
    qty = request.GET.get("qty") or request.POST.get("quantity") or 1
    try:
        qty = int(qty)
        if qty < 1:
            qty = 1
    except:
        qty = 1

    # Check stock availability
    if product.stock <= 0:
        dj_messages.error(request, "Sorry, this product is out of stock.")
        return redirect('user_single_product', slug=slug)

    cart_item, created = Cart.objects.get_or_create(user=request.user,product=product,defaults={'quantity': qty})

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

    return redirect('user_single_product', slug=slug)


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
    return redirect('/user_view_cart')

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
    items = Cart.objects.filter(user=user).select_related("product")

    if not items:
        dj_messages.error(request, "Cart is empty.")
        return redirect("user_view_cart")

    for i in items:
        if i.quantity > i.product.stock:
            dj_messages.error(request, f"Not enough stock for {i.product.product_name}.")
            return redirect("user_checkout")

    addr_id = request.POST.get("selected_address")

    if addr_id:
        try:
            addr = Address.objects.get(id=addr_id, user=user)
        except Address.DoesNotExist:
            dj_messages.error(request, "Invalid address selected.")
            return redirect("user_checkout")
    else:
        fn = request.POST.get("full_name", "").strip()
        ph = request.POST.get("phone", "").strip()
        a1 = request.POST.get("address_line1", "").strip()
        a2 = request.POST.get("address_line2", "").strip()
        ct = request.POST.get("city", "").strip()
        st = request.POST.get("state", "").strip()
        pc = request.POST.get("pincode", "").strip()
        co = request.POST.get("country", "India").strip()

        if not (fn and ph and a1 and ct and st and pc):
            dj_messages.error(request, "Please select an address or fill required fields.")
            return redirect("user_checkout")
        addr = Address.objects.create(
            user=user, full_name=fn, phone=ph,
            address_line1=a1, address_line2=a2 or None,
            city=ct, state=st, pincode=pc, country=co
        )

    final_address = f"{addr.full_name}, {addr.phone}, {addr.address_line1}, "
    if addr.address_line2:
        final_address += f"{addr.address_line2}, "
    final_address += f"{addr.city}, {addr.state} - {addr.pincode}, {addr.country}"
    total = sum(i.product.price * i.quantity for i in items)
    last = Order.objects.order_by("-id").first()
    new_id = last.id + 1 if last else 1
    slug_value = f"order-{new_id}"
    order = Order(id=new_id,user=user,total_amount=total,shipping_address=final_address,status="placed",slug=slug_value)
    order.save()
    for i in items:
        OrderItem.objects.create(order=order, product=i.product, quantity=i.quantity)
        p = i.product
        p.stock -= i.quantity
        p.save()
    items.delete()
    dj_messages.success(request, "Order placed successfully!")
    return redirect("user_orders")

def dummy_payment(request, slug):
    try:
        order = Order.objects.get(slug=slug, user=request.user)
    except Order.DoesNotExist:
        dj_messages.error(request, "Order not found.")
        return redirect("user_view_cart")

    return render(request, "user/dummy_payment.html", {"order": order})


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

# @role_required("customer", login_url="/user_login")
# def add_review(request, slug):
#     try:
#         product = Product.objects.get(slug=slug)
#     except:
#         dj_messages.error(request, "Product not found.")
#         return redirect("user_orders")
#
#     if request.method == "POST":
#         review_text = request.POST.get("review")
#         rating = request.POST.get("rating")
#         review = Review.objects.create(user=request.user,product=product,review=review_text,rating=rating)
#         if request.FILES:
#             for img in request.FILES.getlist("images"):
#                 ReviewImage.objects.create(review=review, review_img=img)
#
#         dj_messages.success(request, "Review added!")
#         return redirect("user_orders")
#
#     return render(request, "user/add_review.html", {"product": product})

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


