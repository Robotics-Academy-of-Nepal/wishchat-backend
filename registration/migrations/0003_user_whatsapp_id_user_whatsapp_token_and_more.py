# Generated by Django 5.1.4 on 2025-01-20 07:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0002_messagequota'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='whatsapp_id',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='whatsapp_token',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='whatsapp_url',
            field=models.TextField(blank=True, max_length=200, null=True),
        ),
    ]
