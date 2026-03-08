from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0007_alter_employee_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='shop',
            name='google_map_link',
            field=models.URLField(blank=True, verbose_name='Google xarita havolasi'),
        ),
        migrations.AddField(
            model_name='shop',
            name='yandex_map_link',
            field=models.URLField(blank=True, verbose_name='Yandex xarita havolasi'),
        ),
        migrations.AlterField(
            model_name='shop',
            name='map_link',
            field=models.URLField(blank=True, verbose_name='Lokatsiya linki (eski)'),
        ),
    ]
