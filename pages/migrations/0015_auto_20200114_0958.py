# Generated by Django 2.1.12 on 2020-01-14 14:58

from django.db import migrations, models
import pages.models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0014_merge_20200114_0955'),
    ]

    operations = [
        migrations.RenameField(
            model_name='request',
            old_name='Emails',
            new_name='target_emails',
        ),
        migrations.AddField(
            model_name='file',
            name='file_object',
            field=models.FileField(default=None, upload_to=pages.models.randomize_path),
        ),
        migrations.AddField(
            model_name='request',
            name='files',
            field=models.ManyToManyField(to='pages.File'),
        ),
    ]