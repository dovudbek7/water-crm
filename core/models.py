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
    shop = models.ForeignKey(Shop, related_name='orders', on_delete=models.PROTECT, verbose_name="Do'kon")
    order_date = models.DateField(default=timezone.localdate, verbose_name='Sana')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    paid_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="To'langan summa",
    )
    note = models.TextField(blank=True, verbose_name='Izoh')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='created_orders',
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
