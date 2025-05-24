from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
import base64
import os

def user_avatar_path(instance, filename):
    # Генерируем уникальное имя файла
    ext = filename.split('.')[-1]
    filename = f"avatar_{instance.user.id}_{instance.user.username}.{ext}"
    return f'avatars/{filename}'

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    avatar = models.ImageField(
        upload_to=user_avatar_path,
        blank=True,
        null=True,
        verbose_name='Аватар'
    )

def __str__(self):
    return f"Профиль {self.user.username}"

def save(self, *args, **kwargs):
    # Удаляем старый файл при обновлении
    if self.pk:
        old = Profile.objects.get(pk=self.pk)
        if old.avatar and old.avatar != self.avatar:
            try:
                old_path = os.path.join(settings.MEDIA_ROOT, old.avatar.name)
                if os.path.exists(old_path):
                    os.remove(old_path)
            except Exception as e:
                print(f"Error deleting old avatar: {str(e)}")
        
    super().save(*args, **kwargs)
    
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:  # Если пользователь только что создан
        Profile.objects.create(user=instance)

class Category(models.Model):
    """Модель категорий меню"""
    name = models.CharField(max_length=100, verbose_name="Название")
    slug = models.SlugField(max_length=100, unique=True)
    icon = models.CharField(
        max_length=50, 
        default='bi-egg-fried', 
        help_text="Иконка из Bootstrap Icons (например, bi-egg-fried)"
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок сортировки"
    )
        
    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['order']
        
    def __str__(self):
        return self.name


class Product(models.Model):
    """Модель товаров/блюд меню"""
    category = models.ForeignKey(
        Category,  # Теперь Category определен выше
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name="Категория"
    )
    name = models.CharField(
        max_length=200,
        verbose_name="Название"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Описание"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена"
    )
    image = models.ImageField(
        upload_to='jpg/',
        default='jpg/default-food.jpg'  # Добавляем значение по умолчанию
    )
    is_available = models.BooleanField(
        default=True,
        verbose_name="Доступно"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )
    
    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ['category__order', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.category.name})"
         
    @property
    def get_image_url(self):
        if self.image and hasattr(self.image, 'url'):
            return self.image.url
        return f"{settings.STATIC_URL}{settings.DEFAULT_IMAGE}"
    
class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('processing', 'В обработке'),
        ('completed', 'Завершен'),
        ('cancelled', 'Отменен'),
    ]
    
    PAYMENT_CHOICES = [
        ('cash', 'Наличными'),
        ('card', 'Картой курьеру'),
        ('online', 'Онлайн оплата'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    total = models.DecimalField(max_digits=10, decimal_places=2)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cash')  # Добавлено
    customer_name = models.CharField(max_length=100, blank=True, null=True)
    comments = models.TextField(blank=True)
    is_demo = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Заказ #{self.id}"
    
    def clean(self):
        if not self.phone:
            raise ValidationError("Телефон обязателен для заполнения")
        if not self.address:
            raise ValidationError("Адрес обязателен для заполнения")
    
    def save(self, *args, **kwargs):
        self.full_clean()  # Вызывает clean() и валидацию всех полей
        super().save(*args, **kwargs)
    
    @property
    def total_price(self):
        return self.price * self.quantity

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('Product', on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Элемент заказа'
        verbose_name_plural = 'Элементы заказа'

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
