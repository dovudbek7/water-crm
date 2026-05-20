from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import Sum
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Product(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True, verbose_name='Mahsulot nomi')
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Narxi (so'm)",
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Mahsulot'
        verbose_name_plural = 'Mahsulotlar'

    def __str__(self):
        return self.name


class Shop(TimeStampedModel):
    name = models.CharField(max_length=160, unique=True, verbose_name="Do'kon nomi")
    address = models.CharField(max_length=255, blank=True, verbose_name='Manzil')
    phone_primary = models.CharField(max_length=25, blank=True, verbose_name='Telefon 1')
    phone_secondary = models.CharField(max_length=25, blank=True, verbose_name='Telefon 2')
    note = models.TextField(blank=True, verbose_name='Izoh')
    photo = models.FileField(upload_to='shops/photos/', blank=True, null=True, verbose_name='Do‘kon rasmi')
    map_link = models.URLField(blank=True, verbose_name='Lokatsiya linki (eski)')
    google_map_link = models.URLField(blank=True, verbose_name='Google xarita havolasi')
    yandex_map_link = models.URLField(blank=True, verbose_name='Yandex xarita havolasi')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        ordering = ('name',)
        verbose_name = "Do'kon"
        verbose_name_plural = "Do'konlar"

    def __str__(self):
        return self.name

    @property
    def total_purchased(self):
        value = self.orders.aggregate(total=Sum('total_amount'))['total']
        return value or Decimal('0')

    @property
    def total_paid(self):
        order_paid = self.orders.aggregate(total=Sum('paid_amount'))['total'] or Decimal('0')
        deposits = self.deposits.aggregate(total=Sum('amount'))['total'] or Decimal('0')
        return order_paid + deposits

    @property
    def balance(self):
        return self.total_paid - self.total_purchased


class Order(TimeStampedModel):
    ORDER_TYPE_PICKUP = 'pickup'
    ORDER_TYPE_DELIVERY = 'delivery'
    ORDER_TYPE_CHOICES = (
        (ORDER_TYPE_PICKUP, 'Zavoddan olib ketish'),
        (ORDER_TYPE_DELIVERY, 'Yetkazib berish'),
    )

    DELIVERY_NEW = 'new'
    DELIVERY_DONE = 'delivered'
    DELIVERY_STATUS_CHOICES = (
        (DELIVERY_NEW, 'Yangi'),
        (DELIVERY_DONE, 'Yetkazildi'),
    )

    shop = models.ForeignKey(Shop, related_name='orders', on_delete=models.PROTECT, verbose_name="Do'kon")
    order_date = models.DateField(default=timezone.localdate, verbose_name='Sana')
    order_type = models.CharField(
        max_length=20,
        choices=ORDER_TYPE_CHOICES,
        default=ORDER_TYPE_PICKUP,
        verbose_name='Buyurtma turi',
    )
    delivery_status = models.CharField(
        max_length=20,
        choices=DELIVERY_STATUS_CHOICES,
        default=DELIVERY_NEW,
        verbose_name='Yetkazish holati',
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    paid_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="To'langan summa",
    )
    note = models.TextField(blank=True, verbose_name='Izoh')
    delivery_received_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    delivery_note = models.TextField(blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='created_orders',
    )
    courier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='delivered_orders',
    )

    class Meta:
        ordering = ('-order_date', '-id')
        verbose_name = 'Buyurtma'
        verbose_name_plural = 'Buyurtmalar'

    def __str__(self):
        return f"#{self.pk} - {self.shop.name}"

    @property
    def remaining_balance(self):
        return self.total_amount - self.paid_amount

    @transaction.atomic
    def recalculate_total(self):
        total = self.items.aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
        self.total_amount = total
        self.save(update_fields=['total_amount', 'updated_at'])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name='Mahsulot')
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)], verbose_name='Soni')
    price_at_sale = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Narxi (so'm)")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))

    class Meta:
        verbose_name = 'Buyurtma elementi'
        verbose_name_plural = 'Buyurtma elementlari'

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'

    def save(self, *args, **kwargs):
        self.total_amount = Decimal(self.quantity) * self.price_at_sale
        super().save(*args, **kwargs)
        self.order.recalculate_total()

    def delete(self, *args, **kwargs):
        order = self.order
        super().delete(*args, **kwargs)
        order.recalculate_total()


class ShopDeposit(TimeStampedModel):
    shop = models.ForeignKey(Shop, related_name='deposits', on_delete=models.CASCADE)
    date = models.DateField(default=timezone.localdate, verbose_name='Sana')
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Miqdor',
    )
    note = models.CharField(max_length=255, blank=True, verbose_name='Izoh')

    class Meta:
        ordering = ('-date', '-id')
        verbose_name = "Depozit"
        verbose_name_plural = "Depozitlar"

    def __str__(self):
        return f"{self.shop.name} +{self.amount}"


class Employee(TimeStampedModel):
    ROLE_COURIER = 'courier'
    ROLE_WORKER = 'worker'
    ROLE_FILLER = 'water_filler'
    ROLE_ORDER_TAKER = 'order_taker'

    ROLE_CHOICES = (
        (ROLE_COURIER, 'Kuryer'),
        (ROLE_WORKER, 'Ishchi'),
        (ROLE_FILLER, "Suv to'ldiruvchi"),
        (ROLE_ORDER_TAKER, 'Buyurtma qabul qiluvchi'),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='employee_profile', on_delete=models.CASCADE)
    photo = models.FileField(upload_to='employees/photos/', blank=True, null=True)
    phone_primary = models.CharField(max_length=25)
    phone_secondary = models.CharField(max_length=25, blank=True)
    role = models.CharField(max_length=30, choices=ROLE_CHOICES)

    class Meta:
        ordering = ('user__first_name', 'user__last_name', 'user__username')

    def __str__(self):
        name = f'{self.user.first_name} {self.user.last_name}'.strip()
        return name or self.user.username

    @property
    def total_orders_taken(self):
        return self.user.created_orders.count()

    @property
    def total_deliveries(self):
        return self.user.delivered_orders.filter(delivery_status=Order.DELIVERY_DONE).count()


class ActionLog(TimeStampedModel):
    ACTION_CREATED = 'created'
    ACTION_UPDATED = 'updated'
    ACTION_DELETED = 'deleted'
    ACTION_SHOP_CREATED = 'shop_created'
    ACTION_ORDER_CREATED = 'order_created'
    ACTION_ORDER_DELIVERED = 'order_delivered'

    ACTION_CHOICES = (
        (ACTION_CREATED, 'Yaratdi'),
        (ACTION_UPDATED, 'Tahrirladi'),
        (ACTION_DELETED, "O'chirdi"),
        (ACTION_SHOP_CREATED, "Do'kon qo'shildi"),
        (ACTION_ORDER_CREATED, "Buyurtma yaratildi"),
        (ACTION_ORDER_DELIVERED, "Buyurtma yetkazildi"),
    )

    employee = models.ForeignKey(Employee, related_name='logs', on_delete=models.SET_NULL, null=True, blank=True)
    actor_name = models.CharField(max_length=150, blank=True)
    action_type = models.CharField(max_length=30, choices=ACTION_CHOICES)
    object_label = models.CharField(max_length=255)
    message = models.CharField(max_length=255)
    target_model = models.CharField(max_length=120, blank=True)
    target_id = models.CharField(max_length=64, blank=True)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return self.message


class UserProfile(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='user_profile', on_delete=models.CASCADE)
    photo = models.FileField(upload_to='users/photos/', blank=True, null=True, verbose_name='Profil rasmi')
    phone_primary = models.CharField(max_length=25, blank=True, verbose_name='Telefon 1')
    phone_secondary = models.CharField(max_length=25, blank=True, verbose_name='Telefon 2')

    class Meta:
        verbose_name = 'Foydalanuvchi profili'
        verbose_name_plural = 'Foydalanuvchi profillari'

    def __str__(self):
        return self.user.get_full_name() or self.user.username
