# Generated by Django 4.0.3 on 2022-07-27 16:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0106_auto_20220727_1243'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='file',
            name='rejection_reason',
        ),
    ]
