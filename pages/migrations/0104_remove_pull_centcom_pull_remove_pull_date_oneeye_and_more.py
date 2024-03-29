# Generated by Django 4.0.3 on 2022-07-19 12:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0103_alter_network_options'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pull',
            name='centcom_pull',
        ),
        migrations.RemoveField(
            model_name='pull',
            name='date_oneeye',
        ),
        migrations.RemoveField(
            model_name='pull',
            name='date_twoeye',
        ),
        migrations.RemoveField(
            model_name='pull',
            name='user_oneeye',
        ),
        migrations.RemoveField(
            model_name='pull',
            name='user_twoeye',
        ),
        migrations.AddField(
            model_name='pull',
            name='pull_deleted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='pull',
            name='queue_for_delete',
            field=models.BooleanField(default=False),
        ),
    ]
