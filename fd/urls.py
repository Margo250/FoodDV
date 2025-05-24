from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Основные страницы
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    
    # Аутентификация
    path('login/', auth_views.LoginView.as_view(
        template_name='fd/login.html',
        redirect_authenticated_user=True
    ), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('register/', views.register, name='register'),
    
    # Меню и корзина
    path('menu/', views.menu_view, name='menu'),
    
    # API для работы с корзиной
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:product_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    path('cart/total/', views.cart_total, name='cart_total'),
    path('cart/details/', views.get_cart_details, name='cart_details'),
    path('cart/count/', views.get_cart_count, name='cart_count'),

    # Оформление заказа
    path('checkout/', views.checkout, name='checkout'),
    path('order/process/', views.process_order, name='process_order'),
    path('order/success/<int:order_id>/', views.order_success, name='order_success'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),

    #Профиль
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('orders/', views.user_orders, name='orders'),
    path('orders/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),
]
