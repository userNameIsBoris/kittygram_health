from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('cats', '0002_cat_owner'),
    ]

    operations = [
        migrations.CreateModel(
            name='Clinic',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120, unique=True)),
                ('address', models.CharField(max_length=255)),
                ('phone', models.CharField(blank=True, max_length=32)),
            ],
        ),
        migrations.CreateModel(
            name='HealthRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('record_type', models.CharField(choices=[('visit', 'Визит'), ('procedure', 'Процедура')], max_length=16)),
                ('date', models.DateField()),
                ('status', models.CharField(choices=[('planned', 'Запланирована'), ('completed', 'Завершена')], default='planned', max_length=16)),
                ('description', models.TextField(blank=True)),
                ('cat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='health_records', to='cats.cat')),
                ('clinic', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='health_records', to='health.clinic')),
            ],
            options={'ordering': ('-date', '-id')},
        ),
    ]
