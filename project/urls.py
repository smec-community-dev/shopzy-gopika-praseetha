"""
URL configuration for project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from Seller import views as views_seller
urlpatterns = [
    path('admin/', admin.site.urls),


    path('seller/register',views_seller.user_register,name="seller_register"),

    path('seller/login',views_seller.user_login,name="seller_login"),
    path('sellerdashboard',views_seller.seller_dashboard,name="seller_dashboard"),
    path('seller/product',views_seller.Create_Product,name="seller_addproduct"),
    path('delete_product/<slug:slug>/', views_seller.product_delete, name='product_delete'),
    path('edit_product/<slug:slug>/', views_seller.edit_product, name='edit_product'),
    path('seller/orders',views_seller.order_list,name='oderslist'),
    path('seller/order/<int:id>/', views_seller.order_single_list, name='orderlist_single'),
    path('seller/product_single/<slug:slug>',views_seller.product_single, name='product_single'),
    path('seller/profile',views_seller.seller_profile,name='profile_update'),
    path('seller/forgott',views_seller.seller_forgott,name='forgott_password'),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
