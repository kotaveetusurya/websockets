# Generated by Django 5.1.2 on 2025-02-27 08:45

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wsapp', '0002_alter_room_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='room',
            name='created_on',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
