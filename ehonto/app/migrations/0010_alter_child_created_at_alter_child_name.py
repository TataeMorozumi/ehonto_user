# Generated by Django 5.1.6 on 2025-03-17 07:10

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0009_alter_child_created_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='child',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='child',
            name='name',
            field=models.CharField(max_length=100),
        ),
    ]
