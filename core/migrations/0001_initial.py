# Generated manually for initial schema
from django.conf import settings
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from decimal import Decimal


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=120, unique=True, verbose_name='Mahsulot nomi')),
                ('price', models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal('0'))], verbose_name="Narxi (so'm)")),
            ],
            options={
                'verbose_name': 'Mahsulot',
                'verbose_name_plural': 'Mahsulotlar',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='Shop',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=160, unique=True, verbose_name="Do'kon nomi")),
                ('address', models.CharField(blank=True, max_length=255, verbose_name='Manzil')),
                ('phone_primary', models.CharField(blank=True, max_length=25, verbose_name='Telefon 1')),
                ('phone_secondary', models.CharField(blank=True, max_length=25, verbose_name='Telefon 2')),
            ],
            options={
                'verbose_name': "Do'kon",
                'verbose_name_plural': "Do'konlar",
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('order_date', models.DateField(default=django.utils.timezone.localdate, verbose_name='Sana')),
                ('total_amount', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=12)),
                ('paid_amount', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal('0'))], verbose_name="To'langan summa")),
                ('note', models.TextField(blank=True, verbose_name='Izoh')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_orders', to=settings.AUTH_USER_MODEL)),
                ('shop', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='orders', to='core.shop', verbose_name="Do'kon")),
            ],
            options={
                'verbose_name': 'Buyurtma',
                'verbose_name_plural': 'Buyurtmalar',
                'ordering': ('-order_date', '-id'),
            },
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name='Soni')),
                ('price_at_sale', models.DecimalField(decimal_places=2, max_digits=12, verbose_name="Narxi (so'm)")),
                ('total_amount', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=12)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='core.order')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.product', verbose_name='Mahsulot')),
            ],
            options={
                'verbose_name': 'Buyurtma elementi',
                'verbose_name_plural': 'Buyurtma elementlari',
            },
        ),
    ]
