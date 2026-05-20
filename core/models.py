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


class Region(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True, verbose_name='Регион номи')

    class Meta:
        ordering = ('name',)
        verbose_name = 'Регион'
        verbose_name_plural = 'Регионлар'

    def __str__(self):
        return self.name


class Product(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True, verbose_name='Маҳсулот номи')
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Нархи (сўм)",
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Маҳсулот'
        verbose_name_plural = 'Маҳсулотлар'

    def __str__(self):
        return self.name


class Shop(TimeStampedModel):
    name = models.CharField(max_length=160, unique=True, verbose_name="Дўкон номи")
    region = models.ForeignKey(Region, null=True, blank=True, on_delete=models.SET_NULL, related_name='shops', verbose_name='Регион')
    address = models.CharField(max_length=255, blank=True, verbose_name='Манзил')
    phone_primary = models.CharField(max_length=25, blank=True, verbose_name='Телефон 1')
    phone_secondary = models.CharField(max_length=25, blank=True, verbose_name='Телефон 2')
    note = models.TextField(blank=True, verbose_name='Изоҳ')
    photo = models.FileField(upload_to='shops/photos/', blank=True, null=True, verbose_name='Дўкон расми')
    map_link = models.URLField(blank=True, verbose_name='Локация линқи (эски)')
    google_map_link = models.URLField(blank=True, verbose_name='Google харита ҳаволаси')
    yandex_map_link = models.URLField(blank=True, verbose_name='Yandex харита ҳаволаси')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        ordering = ('name',)
        verbose_name = "Дўкон"
        verbose_name_plural = "Дўконлар"

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
        (ORDER_TYPE_PICKUP, 'Заводдан олиб кетиш'),
        (ORDER_TYPE_DELIVERY, 'Етказиб бериш'),
    )

    DELIVERY_NEW = 'new'
    DELIVERY_DONE = 'delivered'
    DELIVERY_CLOSED = 'closed'
    DELIVERY_STATUS_CHOICES = (
        (DELIVERY_NEW, 'Янги'),
        (DELIVERY_DONE, 'Етказилди'),
        (DELIVERY_CLOSED, 'Ёпиқ'),
    )

    shop = models.ForeignKey(Shop, related_name='orders', on_delete=models.PROTECT, verbose_name="Дўкон")
    order_date = models.DateField(default=timezone.localdate, verbose_name='Сана')
    order_type = models.CharField(
        max_length=20,
        choices=ORDER_TYPE_CHOICES,
        default=ORDER_TYPE_PICKUP,
        verbose_name='Буюртма тури',
    )
    delivery_status = models.CharField(
        max_length=20,
        choices=DELIVERY_STATUS_CHOICES,
        default=DELIVERY_NEW,
        verbose_name='Етказиш ҳолати',
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    paid_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Тўланган сумма",
    )
    note = models.TextField(blank=True, verbose_name='Изоҳ')
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
        verbose_name = 'Буюртма'
        verbose_name_plural = 'Буюртмалар'

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
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name='Маҳсулот')
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)], verbose_name='Сони')
    price_at_sale = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Нархи (сўм)")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))

    class Meta:
        verbose_name = 'Буюртма элементи'
        verbose_name_plural = 'Буюртма элементлари'

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
    date = models.DateField(default=timezone.localdate, verbose_name='Сана')
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Миқдор',
    )
    note = models.CharField(max_length=255, blank=True, verbose_name='Изоҳ')

    class Meta:
        ordering = ('-date', '-id')
        verbose_name = "Depozit"
        verbose_name_plural = "Депозитлар"

    def __str__(self):
        return f"{self.shop.name} +{self.amount}"


class Employee(TimeStampedModel):
    ROLE_COURIER = 'courier'
    ROLE_WORKER = 'worker'
    ROLE_FILLER = 'water_filler'
    ROLE_ORDER_TAKER = 'order_taker'

    ROLE_CHOICES = (
        (ROLE_COURIER, 'Курер'),
        (ROLE_WORKER, 'Ишчи'),
        (ROLE_FILLER, "Сув тўлдирувчи"),
        (ROLE_ORDER_TAKER, 'Буюртма қабул қилувчи'),
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
        (ACTION_CREATED, 'Яратди'),
        (ACTION_UPDATED, 'Таҳрирлади'),
        (ACTION_DELETED, "Ўчирди"),
        (ACTION_SHOP_CREATED, "Дўкон қўшилди"),
        (ACTION_ORDER_CREATED, "Буюртма яратилди"),
        (ACTION_ORDER_DELIVERED, "Буюртма етказилди"),
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
    photo = models.FileField(upload_to='users/photos/', blank=True, null=True, verbose_name='Профил расми')
    phone_primary = models.CharField(max_length=25, blank=True, verbose_name='Telefon 1')
    phone_secondary = models.CharField(max_length=25, blank=True, verbose_name='Telefon 2')
    telegram_phone = models.CharField(max_length=25, blank=True, verbose_name='Telegram телефони')
    telegram_link_token = models.CharField(max_length=80, blank=True, verbose_name='Telegram token')
    telegram_chat_id = models.CharField(max_length=64, blank=True, verbose_name='Telegram chat ID')
    telegram_username = models.CharField(max_length=150, blank=True, verbose_name='Telegram username')
    telegram_connected_at = models.DateTimeField(null=True, blank=True, verbose_name='Telegram уланган вақт')

    class Meta:
        verbose_name = 'Фойдаланувчи профили'
        verbose_name_plural = 'Фойдаланувчи профиллари'

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    @property
    def telegram_connected(self):
        return bool(self.telegram_chat_id)
