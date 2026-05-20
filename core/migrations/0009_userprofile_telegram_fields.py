from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0008_shop_google_yandex_links'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='telegram_chat_id',
            field=models.CharField(blank=True, max_length=64, verbose_name='Telegram chat ID'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='telegram_connected_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Telegram ulangan vaqt'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='telegram_link_token',
            field=models.CharField(blank=True, max_length=80, verbose_name='Telegram token'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='telegram_phone',
            field=models.CharField(blank=True, max_length=25, verbose_name='Telegram telefoni'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='telegram_username',
            field=models.CharField(blank=True, max_length=150, verbose_name='Telegram username'),
        ),
    ]
