from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0004_employee_actionlog_delivery_location'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actionlog',
            name='employee',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='logs', to='core.employee'),
        ),
        migrations.AddField(
            model_name='actionlog',
            name='actor_name',
            field=models.CharField(blank=True, max_length=150),
        ),
    ]
