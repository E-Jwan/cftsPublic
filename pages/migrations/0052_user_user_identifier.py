# Generated by Django 2.1.12 on 2021-05-28 16:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0051_user_is_centcom'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='user_identifier',
            field=models.CharField(default='00000.0000.0.0000000', max_length=50),
        ),
    ]