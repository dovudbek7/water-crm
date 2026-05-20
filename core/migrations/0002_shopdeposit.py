from decimal import Decimal

from django.db import migrations, models
import django.core.validators
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShopDeposit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('date', models.DateField(default=django.utils.timezone.localdate, verbose_name='Sana')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))], verbose_name='Miqdor')),
                ('note', models.CharField(blank=True, max_length=255, verbose_name='Izoh')),
                ('shop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deposits', to='core.shop')),
            ],
            options={
                'verbose_name': 'Depozit',
                'verbose_name_plural': 'Depozitlar',
                'ordering': ('-date', '-id'),
            },
        ),
    ]
