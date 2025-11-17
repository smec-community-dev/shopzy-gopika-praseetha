from django.shortcuts import render,redirect
from pyexpat.errors import messages

from Core.models import User,Category,SubCategory
from Seller.models import Product
from .models import Customer,Review,ReviewImage,Wishlist
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
        messages.error(request,"Product not found")
        return redirect('/user_home')
    images = product.images.all()
    wishlisted = Wishlist.objects.filter(user=request.user, product=product).exists()
    return render(request, 'user/user_single_product.html', {'product': product,'images': images,'wishlisted': wishlisted})

@login_required(login_url='/user_login')
def user_add_wishlist(request, slug):
    product = Product.objects.get(slug=slug)
    try:
        data = Wishlist.objects.get(user=request.user, product=product)
        data.delete()
    except Wishlist.DoesNotExist:
        w = Wishlist()
        w.user = request.user
        w.product = product
        w.save()
    return redirect('user_single_product', slug=slug)

@login_required(login_url='/user_login')
def user_view_wishlist(request):
    data = Wishlist.objects.filter(user=request.user)
    return render(request, 'user/user_wishlist.html', {'data': data})

@login_required(login_url='/user_login')
def user_remove_wishlist(request, id):
    data = Wishlist.objects.get(id=id)
    data.delete()
    return redirect('user_view_wishlist')

@login_required(login_url='/user_login')
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

@login_required(login_url='//user_login')
def user_logout(request):
    logout(request)
    return redirect('/user_home')







