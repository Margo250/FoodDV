from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from .forms import RegisterForm
from django.conf import settings
from .models import Category, Product
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from .models import Order, OrderItem, Profile
from django.db import transaction
import json
import os
from datetime import datetime
import logging
logger = logging.getLogger(__name__)

def home(request):
    return render(request, 'fd/home.html')

def about(request):
    return render(request, 'fd/about.html')

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'fd/register.html', {'form': form})

def custom_logout(request):
    logout(request)
    messages.info(request, 'Вы вышли из системы')
    return redirect('home')

def menu_view(request):
    try:
        categories = {
            cat.id: {
                'name': cat.name,
                'icon': cat.icon
            } for cat in Category.objects.all()
        }
        
        products = []
        for product in Product.objects.filter(is_available=True):
            product_data = {
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': float(product.price),
                'category': product.category_id
            }
            
            if product.image and hasattr(product.image, 'url'):
                product_data['image'] = product.image.url
            else:
                product_data['image'] = ''
            
            products.append(product_data)
        
        return render(request, 'fd/menu.html', {
            'categories': categories,
            'products': products
        })
        
    except Exception as e:
        print(f"Error in menu_view: {str(e)}")
        return render(request, 'fd/menu.html', {
            'categories': {},
            'products': [],
            'error': 'Произошла ошибка при загрузке меню'
        })

def get_cart(request):
    """Возвращает текущую корзину, гарантируя что это словарь"""
    if not isinstance(request.session.get('cart'), dict):
        request.session['cart'] = {}
    return request.session['cart']

@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})
    
    product_id_str = str(product_id)
    cart[product_id_str] = cart.get(product_id_str, 0) + 1
    request.session['cart'] = cart
    request.session.modified = True
    
    return JsonResponse({
        'success': True,
        'total_items': sum(cart.values()),
        'product_name': product.name
    })

@require_POST
def remove_from_cart(request, product_id):
    try:
        cart = request.session.get('cart', {})
        product_id_str = str(product_id)
        
        if product_id_str in cart:
            # Получаем продукт перед удалением для расчета общей суммы
            product = get_object_or_404(Product, id=product_id)
            removed_quantity = cart[product_id_str]
            removed_total = float(product.price) * removed_quantity
            
            del cart[product_id_str]
            request.session['cart'] = cart
            request.session.modified = True
            
            # Пересчитываем общую сумму
            cart_total = sum(
                float(Product.objects.get(id=int(id)).price) * qty 
                for id, qty in cart.items()
            )
            
            return JsonResponse({
                'success': True,
                'cart_total': cart_total,
                'total_items': sum(cart.values()),
                'removed_item': product_id
            })
        
        return JsonResponse({
            'success': False,
            'error': 'Товар не найден в корзине'
        }, status=404)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
    
@require_POST
def update_cart_item(request, product_id):
    try:
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))
        
        if quantity < 1:
            return JsonResponse({'error': 'Количество не может быть меньше 1'}, status=400)
        
        cart = request.session.get('cart', {})
        product_id_str = str(product_id)
        
        if product_id_str in cart:
            cart[product_id_str] = quantity
            request.session['cart'] = cart
            request.session.modified = True
            
            product = get_object_or_404(Product, id=product_id)
            item_total = float(product.price) * quantity
            cart_total = sum(
                float(Product.objects.get(id=int(id)).price) * qty 
                for id, qty in cart.items()
            )
            
            return JsonResponse({
                'success': True,
                'new_quantity': quantity,
                'item_total': round(item_total, 2),
                'cart_total': round(cart_total, 2),
                'total_items': sum(cart.values())
            })
        
        return JsonResponse({'error': 'Товар не найден'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_POST
def clear_cart(request):
    """Полная очистка корзины с гарантированным результатом"""
    try:
        request.session['cart'] = {}
        request.session.modified = True
        request.session.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Корзина полностью очищена',
            'total_items': 0,
            'cart_state': request.session.get('cart', {})
        })
    except Exception as e:
        print(f"Ошибка очистки корзины: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Не удалось очистить корзину',
            'debug': str(e)
        }, status=500)

@require_http_methods(["GET"])
def cart_total(request):
    """Упрощенный и безопасный счетчик корзины"""
    try:
        cart = request.session.get('cart', {})
        return JsonResponse({
            'count': sum(int(qty) for qty in cart.values() if str(qty).isdigit())
        })
    except Exception:
        return JsonResponse({'count': 0})
    
@never_cache
@require_GET
def get_cart_count(request):
    """Возвращает только количество товаров в корзине"""
    cart = request.session.get('cart', {})
    count = sum(cart.values()) if isinstance(cart, dict) else 0
    return JsonResponse({'count': count})

def cart_view(request):
    cart = request.session.get('cart', {})
    cart_items = []
    
    products = Product.objects.filter(
        id__in=cart.keys(),
        is_available=True
    ).select_related('category')
    
    for product in products:
        quantity = cart.get(str(product.id), 0)
        if quantity > 0:
            cart_items.append({
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'price': float(product.price),
                    'image_url': product.get_image_url,
                    'description': product.description,
                    'category': product.category.name
                },
                'quantity': quantity,
                'total': float(product.price) * quantity
            })
    
    return render(request, 'fd/cart.html', {
        'cart_items': cart_items,
        'total': sum(item['total'] for item in cart_items)
    })
    
def get_cart_details(request):
    """Получение деталей корзины для AJAX-запросов"""
    cart = get_cart(request)
    product_ids = cart.keys()
    products = Product.objects.filter(id__in=product_ids)
    
    items = []
    for product in products:
        quantity = cart.get(str(product.id), 0)
        if quantity > 0:
            items.append({
                'id': product.id,
                'name': product.name,
                'price': float(product.price),
                'quantity': quantity,
                'total': float(product.price) * quantity,
                'image': product.image.url if product.image else ''
            })
    
    return JsonResponse({
        'items': items,
        'total': sum(item['total'] for item in items),
        'total_items': sum(cart.values()) if cart else 0
    })

def checkout(request):
    if not request.session.get('cart'):
        return redirect('menu')
    
    cart_items = []
    total = 0
    
    cart = request.session.get('cart', {})
    products = Product.objects.filter(id__in=cart.keys())
    
    for product in products:
        quantity = cart.get(str(product.id), 0)
        if quantity > 0:
            item_total = product.price * quantity
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'total': item_total
            })
            total += item_total
    
    return render(request, 'fd/checkout.html', {
        'cart_items': cart_items,
        'total': total
    })
    
@require_POST
@login_required
def process_order(request):
    try:
        data = json.loads(request.body)
        
        # Валидация обязательных полей
        if not data.get('phone') or not data.get('address'):
            return JsonResponse({
                'success': False,
                'error': 'Телефон и адрес обязательны для заполнения'
            }, status=400)
        
        with transaction.atomic():
            # Создаем заказ
            order = Order.objects.create(
                user=request.user,
                customer_name=data.get('name', request.user.get_full_name() or request.user.username),
                phone=data['phone'],
                address=data['address'],
                total=0,
                payment_method=data.get('payment', 'cash'),
                comments=data.get('comment', ''),
                is_demo=False
            )
            
            # Добавляем товары из корзины
            cart = request.session.get('cart', {})
            products = Product.objects.in_bulk([int(id) for id in cart.keys()])
            
            order_items = []
            total = 0
            for product_id, quantity in cart.items():
                product = products[int(product_id)]
                order_items.append(OrderItem(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=product.price
                ))
                total += product.price * quantity
            
            OrderItem.objects.bulk_create(order_items)
            order.total = total
            order.save()
            
            # Очищаем корзину
            request.session['cart'] = {}
            request.session.modified = True
            
            return JsonResponse({
                'success': True,
                'order_id': order.id
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def order_success(request, order_id):
    return render(request, 'fd/order_success.html', {
        'order_id': order_id
    })

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'fd/order_detail.html', {
        'order': order,
        'items': order.items.all()
    })

@login_required
def profile(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user)
    
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    return render(request, 'fd/profile.html', {
        'profile': profile,
        'orders': orders
    })

@login_required
def update_profile(request):
    if request.method == 'POST':
        try:
            profile = request.user.profile
            
            # Обновляем текстовые данные
            profile.phone = request.POST.get('phone', '')
            profile.address = request.POST.get('address', '')
            
            # Обработка аватарки
            if 'avatar' in request.FILES:
                # Удаляем старый аватар, если он существует
                if profile.avatar:
                    try:
                        old_path = os.path.join(settings.MEDIA_ROOT, profile.avatar.name)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    except Exception as e:
                        print(f"Error deleting old avatar: {str(e)}")
                
                # Сохраняем новый аватар
                new_avatar = request.FILES['avatar']
                profile.avatar.save(
                    f"avatar_{datetime.now().strftime('%Y%m%d%H%M%S')}_{new_avatar.name}",
                    new_avatar
                )
            
            # Обработка удаления аватарки
            elif request.POST.get('avatar-clear') == 'on':
                if profile.avatar:
                    try:
                        old_path = os.path.join(settings.MEDIA_ROOT, profile.avatar.name)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    except Exception as e:
                        print(f"Error deleting avatar: {str(e)}")
                    profile.avatar = None
            
            # Сохраняем изменения
            profile.save()
            
            # Возвращаем успешный ответ
            return JsonResponse({
                'success': True,
                'avatar_url': profile.avatar.url if profile.avatar else '',
                'message': 'Профиль успешно обновлен!'
            })
            
        except Exception as e:
            print(f"Server error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Произошла ошибка при сохранении данных'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Недопустимый метод запроса'
    }, status=400)
    
@login_required
def user_orders(request):
    # Получаем заказы из базы данных для текущего пользователя
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    # Добавляем текстовое описание статусов
    for order in orders:
        order.status_text = order.get_status_display()
    
    return render(request, 'fd/order.html', {
        'orders': orders
    })

@login_required
@require_POST
def cancel_order(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user)
        
        if order.status != 'new':
            return JsonResponse({
                'success': False,
                'error': 'Можно отменить только новые заказы'
            }, status=400)
            
        order.status = 'cancelled'
        order.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Заказ успешно отменен'
        })
        
    except Order.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Заказ не найден'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def get_status_text(status):
    status_map = {
        'new': 'В обработке',
        'preparing': 'Готовится',
        'delivery': 'В пути',
        'completed': 'Завершен',
        'cancelled': 'Отменен'
    }
    return status_map.get(status, 'Неизвестен')
