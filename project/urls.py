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
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from User import views as view_user


urlpatterns = [
    path('admin/', admin.site.urls),
    path('',view_user.user_home),
    path('user_register/',view_user.user_register,name='user_register'),
    path('user_login/',view_user.user_login,name='user_login'),
    path('user_home/',view_user.user_home,name='user_home'),
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
    path('place_order/', view_user.place_order, name='place_order'),
    path("dummy_payment/<slug:slug>/", view_user.dummy_payment, name="dummy_payment"),
    path('user_dashboard/', view_user.user_dashboard, name='user_dashboard'),
    path('user_orders/', view_user.user_orders, name='user_orders'),
    path("add_review/<slug:slug>/", view_user.add_review, name="add_review"),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
