from decimal import Decimal

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0003_shop_note'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='shop',
            name='latitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='shop',
            name='longitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='shop',
            name='map_link',
            field=models.URLField(blank=True, verbose_name='Google Maps link'),
        ),
        migrations.AddField(
            model_name='shop',
            name='photo',
            field=models.FileField(blank=True, null=True, upload_to='shops/photos/', verbose_name='Do‘kon rasmi'),
        ),
        migrations.AddField(
            model_name='order',
            name='courier',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='delivered_orders', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='order',
            name='delivered_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='delivery_note',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='order',
            name='delivery_received_amount',
            field=models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=12),
        ),
        migrations.AddField(
            model_name='order',
            name='delivery_status',
            field=models.CharField(choices=[('new', 'Yangi'), ('delivered', 'Yetkazildi')], default='new', max_length=20, verbose_name='Yetkazish holati'),
        ),
        migrations.AddField(
            model_name='order',
            name='order_type',
            field=models.CharField(choices=[('pickup', 'Zavoddan olib ketish'), ('delivery', 'Yetkazib berish')], default='pickup', max_length=20, verbose_name='Buyurtma turi'),
        ),
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('photo', models.FileField(blank=True, null=True, upload_to='employees/photos/')),
                ('phone_primary', models.CharField(max_length=25)),
                ('phone_secondary', models.CharField(blank=True, max_length=25)),
                ('role', models.CharField(choices=[('courier', 'Courier'), ('worker', 'Worker'), ('water_filler', 'Water Filler'), ('order_taker', 'Order Taker')], max_length=30)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='employee_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ('user__first_name', 'user__last_name', 'user__username')},
        ),
        migrations.CreateModel(
            name='ActionLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('action_type', models.CharField(choices=[('shop_created', "Do'kon qo'shildi"), ('order_created', 'Buyurtma yaratildi'), ('order_delivered', 'Buyurtma yetkazildi')], max_length=30)),
                ('object_label', models.CharField(max_length=255)),
                ('message', models.CharField(max_length=255)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='core.employee')),
            ],
            options={'ordering': ('-created_at',)},
        ),
    ]
