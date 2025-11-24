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
from tkinter.font import names

from django.contrib import admin




from django.urls import include

from django.urls import path

from django.conf import settings
from django.conf.urls.static import static
from User import views as view_user



from Seller import views as views_seller
from Core import views as view_admin
urlpatterns = [
    path('admin/', admin.site.urls),
    path('',view_user.home, name="home"),



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
    path('seller/logout',views_seller.seller_logout,name='seller_logout'),
    path('seller/addform',views_seller.Create_products_form,name='addform'),
    path('order/<int:order_id>/update-status/', views_seller.update_order_status, name='update_order_status'),
    path('profile/password_change/', views_seller.seller_password_change, name='seller_password_change'),
    path('profile/update/', views_seller.seller_profile_update, name='seller_profile_update'),
    path('profile/delete/', views_seller.seller_delete_profile, name='seller_delete_profile'),
    path('accounts/', include('allauth.urls')),
    path('login/admin',view_admin.admin_login,name='admin_login'),
    path('dashbaords/admin',view_admin.admin_dashboard, name='admin_dashboard'),
    path('admin/logout/', view_admin.admin_logout, name='admin_logout'),
    path('create-admin/', view_admin.create_temp_admin, name='create_admin'),
    path('users/admin/', view_admin.user_management, name='user_management'),
    path('product/admin/', view_admin.product_management, name='product_management'),
    path('orders/admin/', view_admin.order_management, name='order_management'),
    path('sellers/admin/', view_admin.seller_management, name='seller_management'),
    path('analytics/admin/', view_admin.analytics, name='analytics'),
    path('settings/admin/', view_admin.admin_settings, name='admin_settings'),
    path('users/admin/toggle/<int:user_id>/', view_admin.toggle_user_status, name='toggle_user_status'),
    path('orders/admin/update-status/<int:order_id>/', view_admin.update_order_status, name='update_order_status'),
    path('orders/admin/viewdetails/<int:order_id>/', view_admin.order_detail, name='order_detail'),
    path('users/admin/update-role/<int:user_id>/', view_admin.update_user_role, name='update_user_role'),
    path('users/admin/delete/<int:user_id>/', view_admin.delete_user, name='delete_user'),
    path('products/admin/toggle-status/<int:product_id>/', view_admin.toggle_product_status, name='toggle_product_status'),
    path('orders/admin/<int:order_id>/', view_admin.order_detail, name='order_detail'),
    path('sellers/admin/toggle-status/<int:seller_id>/', view_admin.toggle_seller_status, name='toggle_seller_status'),
    path('reviews/', view_admin.review_management, name='review_management'),
    path('reviews/<int:review_id>/', view_admin.review_detail, name='review_detail'),
    path('reviews/<int:review_id>/delete/', view_admin.delete_review, name='delete_review'),





    path('user_register/',view_user.user_register,name='user_register'),
    path('user_login/',view_user.user_login,name='user_login'),


    # path("category/<slug:slug>/", view_user.category_products, name="category_products"),

    path('user_single_product/<slug:slug>/',view_user.user_single_product,name='user_single_product'),
    path('add_wishlist/<slug:slug>/', view_user.user_add_wishlist, name='add_wishlist'),
    path('user_view_wishlist/', view_user.user_view_wishlist, name='user_view_wishlist'),
    path('user_remove_wishlist/<int:id>/', view_user.user_remove_wishlist, name='user_remove_wishlist'),
    path('user_logout/',view_user.user_logout,name='user_logout'),
    path('user_add_to_cart/<slug:slug>/',view_user.user_add_to_cart,name='user_add_to_cart'),
    path('user_view_cart/',view_user.user_view_cart,name='user_view_cart'),
    path('user_remove_from_cart/<int:id>/',view_user.user_remove_from_cart,name='user_remove_from_cart'),
    path('user_update_cart/<int:id>/',view_user.user_update_cart,name='user_update_cart'),
    path('user_checkout/', view_user.user_checkout, name='user_checkout'),
    path('update_checkout_qty/<int:id>/', view_user.user_update_checkout_quantity, name='user_update_checkout_quantity'),
    path("place_order/", view_user.place_order, name="place_order"),
    path('user_dashboard/', view_user.user_dashboard, name='user_dashboard'),
    path('user_orders/', view_user.user_orders, name='user_orders'),
    path("add_review/<slug:slug>/", view_user.add_review, name="add_review"),

    path('shop/',view_user.shop_page,name='shop_page'),
    path("order/cancel/<int:order_id>/", view_user.cancel_order, name="cancel_order"),
    path("user_profile_edit/", view_user.user_profile_edit, name="user_profile_edit"),
    path('user_buy_now/<slug:slug>/', view_user.user_buy_now, name='user_buy_now'),
    path("order_success/<slug:order_slug>/", view_user.order_success, name="order_success"),
    path("save_address/", view_user.save_address, name="save_address"),
    path("delete_address/<int:address_id>/", view_user.delete_address, name="delete_address"),
    path("set_default_address/<int:address_id>/", view_user.set_default_address, name="set_default_address"),
    path('change_password/', view_user.change_password_view, name='change_password'),
    path('user_about/',view_user.user_about,name='user_about'),
    # path("accounts/", include("allauth.urls")),
    path('contact/',view_user.contact,name='contact'),
    path("create_razorpay_order/", view_user.create_razorpay_order, name="create_razorpay_order"),
]








if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
