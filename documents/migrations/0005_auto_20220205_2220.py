# Generated by Django 2.2.12 on 2022-02-05 22:20

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0004_auto_20220205_2204'),
    ]

    operations = [
        migrations.AddField(
            model_name='documents',
            name='created_date',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='documents',
            name='modified_date',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
