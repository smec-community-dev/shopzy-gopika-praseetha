from django.shortcuts import render,redirect
from django.contrib import messages as dj_messages
from Core.models import User,Category,SubCategory
from Seller.models import Product
from decorators.decorators import role_required
from .models import Customer,Review,ReviewImage,Wishlist,Cart,Order,OrderItem
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
def user_add_review(request, slug):
    product = Product.objects.get(slug=slug)
    if request.method == "POST":
        review = Review()
        review.user = request.user
        review.product = product
        review.review = request.POST.get("review")
        review.rating = request.POST.get("rating")
        review.save()

        for img in request.FILES.getlist("images"):
            ri = ReviewImage()
            ri.review = review
            ri.review_img = img
            ri.save()
    return redirect('user_single_product', slug=slug)

@role_required("customer", login_url="/user_login")
def user_logout(request):
    logout(request)
    return redirect('/user_home')

@role_required("customer", login_url="/user_login")
def user_add_to_cart(request, slug):
    # Get product
    try:
        product = Product.objects.get(slug=slug)
    except Product.DoesNotExist:
        return redirect("/user_home")

    # Quantity from GET or POST
    qty = request.GET.get("qty") or request.POST.get("quantity") or 1

    # Validate quantity
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

    # Get or create cart item
    cart_item, created = Cart.objects.get_or_create(
        user=request.user,
        product=product,
        defaults={'quantity': qty}
    )

    # If item already in cart, add to existing qty
    if not created:
        new_qty = cart_item.quantity + qty

        # Stock limit
        if new_qty > product.stock:
            new_qty = product.stock
            dj_messages.info(request, f"Only {product.stock} in stock. Quantity adjusted.")

        cart_item.quantity = new_qty
        cart_item.save()

    else:
        # First time adding — still check stock
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


# @role_required("customer", login_url="/user_login")
# def user_update_cart(request, id):
#     try:
#         item = Cart.objects.get(id=id, user=request.user)
#     except Cart.DoesNotExist:
#         return redirect('/user_view_cart')
#     qty = request.POST.get("quantity", 1)
#     try:
#         qty = int(qty)
#         if qty < 1:
#             qty = 1
#     except:
#         qty = 1
#     item.quantity = qty
#     item.save()
#     return redirect('/user_view_cart')

# @login_required(login_url='/user_login')
# def user_move_to_cart(request, id):
#     try:
#         wish_item = Wishlist.objects.get(id=id, user=request.user)
#     except Wishlist.DoesNotExist:
#         return redirect('/user_view_wishlist')
#     product = wish_item.product
#     cart_item, created = Cart.objects.get_or_create(user=request.user,product=product)
#     if not created:
#         cart_item.quantity += 1
#     cart_item.save()
#     wish_item.delete()
#     return redirect('/user_view_cart')
#
# @login_required(login_url='/user_login')
# def user_review_cartitem(request):
#     items = Cart.objects.filter(user=request.user)
#     total = sum(i.product.price * i.quantity for i in items)
#     return render(request, 'user/user_review_cartitem.html', {'items': items,'total': total})

@role_required("customer", login_url="/user_login")
def user_checkout(request):

    items = Cart.objects.filter(user=request.user).select_related("product")

    for item in items:
        item.subtotal = item.product.price * item.quantity

    total = sum(item.subtotal for item in items)

    return render(request, "user/user_checkout.html", {
        "items": items,
        "total": total
    })

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

    items = Cart.objects.filter(user=request.user).select_related("product")

    if not items:
        dj_messages.error(request, "Cart is empty.")
        return redirect("user_view_cart")

    for item in items:
        if item.quantity > item.product.stock:
            dj_messages.error(request, f"Not enough stock for {item.product.product_name}.")
            return redirect("user_checkout")

    shipping_address = request.POST.get("shipping_address", "").strip()

    if shipping_address == "":
        dj_messages.error(request, "Shipping address is required.")
        return redirect("user_checkout")

    total_amount = sum(item.product.price * item.quantity for item in items)

    order = Order.objects.create(
        user=request.user,
        total_amount=total_amount,
        shipping_address=shipping_address,
        status="placed"
    )

    for item in items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity
        )

        product = item.product
        product.stock -= item.quantity
        product.save()

    items.delete()

    dj_messages.success(request, "Order placed successfully!")
    return redirect("order_summary", id=order.id)


@role_required("customer", login_url="/user_login")
def order_summary(request, id):
    try:
        order = Order.objects.get(id=id, user=request.user)
    except Order.DoesNotExist:
        return redirect('user_home')

    return render(request, "user/order_summary.html", {"order": order})

@login_required(login_url='/user_login')
def user_dashboard(request):
    return render(request, 'user/user_dashboard.html')









