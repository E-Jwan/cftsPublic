# Generated by Django 4.0.3 on 2022-07-27 16:43

from django.db import migrations

def rejection_migrate(apps, schema_editor):
    File = apps.get_model("pages", "File")
    db_alias = schema_editor.connection.alias

    for file in File.objects.using(db_alias).filter(rejection_reason__isnull=False):
        file.rejection_reasons.add(file.rejection_reason)
        file.save()


def reverseFunction(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0105_file_rejection_reasons_alter_file_rejection_reason'),
    ]

    operations = [
        migrations.RunPython(rejection_migrate, reverseFunction)
    ]
