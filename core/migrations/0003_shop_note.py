from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0002_shopdeposit'),
    ]

    operations = [
        migrations.AddField(
            model_name='shop',
            name='note',
            field=models.TextField(blank=True, verbose_name='Izoh'),
        ),
    ]
