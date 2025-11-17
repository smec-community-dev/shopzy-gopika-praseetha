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
    path('user_single_product/<slug:slug>',view_user.user_single_product,name='user_single_product'),
    path('add_review/<slug:slug>/', view_user.user_add_review, name='user_add_review'),
    path('add_wishlist/<slug:slug>/', view_user.user_add_wishlist, name='add_wishlist'),
    path('user_view_wishlist/', view_user.user_view_wishlist, name='user_view_wishlist'),
    path('user_remove_wishlist/<int:id>/', view_user.user_remove_wishlist, name='user_remove_wishlist'),
    path('user_logout/',view_user.user_logout,name='user_logout')


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
