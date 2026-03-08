from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0005_actionlog_actor_nullable'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='actionlog',
            name='details',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='actionlog',
            name='target_id',
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name='actionlog',
            name='target_model',
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AlterField(
            model_name='actionlog',
            name='action_type',
            field=models.CharField(choices=[('created', 'Yaratdi'), ('updated', 'Tahrirladi'), ('deleted', "O'chirdi"), ('shop_created', "Do'kon qo'shildi"), ('order_created', 'Buyurtma yaratildi'), ('order_delivered', 'Buyurtma yetkazildi')], max_length=30),
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('photo', models.FileField(blank=True, null=True, upload_to='users/photos/', verbose_name='Profil rasmi')),
                ('phone_primary', models.CharField(blank=True, max_length=25, verbose_name='Telefon 1')),
                ('phone_secondary', models.CharField(blank=True, max_length=25, verbose_name='Telefon 2')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='user_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Foydalanuvchi profili',
                'verbose_name_plural': 'Foydalanuvchi profillari',
            },
        ),
    ]
