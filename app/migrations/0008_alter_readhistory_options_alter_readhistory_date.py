# Generated by Django 5.1.7 on 2025-03-30 06:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0007_readhistory'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='readhistory',
            options={},
        ),
        migrations.AlterField(
            model_name='readhistory',
            name='date',
            field=models.DateField(),
        ),
    ]
