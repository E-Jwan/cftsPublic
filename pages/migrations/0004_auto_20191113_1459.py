# Generated by Django 2.1.12 on 2019-11-13 19:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0003_file_path'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='classification',
            options={'ordering': ['sort_order']},
        ),
        migrations.RenameField(
            model_name='classification',
            old_name='Abbrev',
            new_name='abbrev',
        ),
        migrations.RenameField(
            model_name='classification',
            old_name='Classification_id',
            new_name='classification_id',
        ),
        migrations.RenameField(
            model_name='classification',
            old_name='FullName',
            new_name='full_name',
        ),
        migrations.RenameField(
            model_name='classification',
            old_name='SortOrder',
            new_name='sort_order',
        ),
        migrations.RenameField(
            model_name='email',
            old_name='Address',
            new_name='address',
        ),
        migrations.RenameField(
            model_name='email',
            old_name='Email_id',
            new_name='email_id',
        ),
        migrations.RenameField(
            model_name='file',
            old_name='Classification',
            new_name='classification',
        ),
        migrations.RenameField(
            model_name='file',
            old_name='File_id',
            new_name='file_id',
        ),
        migrations.RenameField(
            model_name='file',
            old_name='Filename',
            new_name='filename',
        ),
        migrations.RenameField(
            model_name='file',
            old_name='Path',
            new_name='path',
        ),
        migrations.RenameField(
            model_name='file',
            old_name='Size',
            new_name='size',
        ),
        migrations.RenameField(
            model_name='network',
            old_name='Classifications',
            new_name='classifications',
        ),
        migrations.RenameField(
            model_name='network',
            old_name='Name',
            new_name='name',
        ),
        migrations.RenameField(
            model_name='network',
            old_name='Network_id',
            new_name='network_id',
        ),
        migrations.RenameField(
            model_name='request',
            old_name='DateComplete',
            new_name='date_complete',
        ),
        migrations.RenameField(
            model_name='request',
            old_name='DateCreated',
            new_name='date_created',
        ),
        migrations.RenameField(
            model_name='request',
            old_name='DateOneEye',
            new_name='date_oneeye',
        ),
        migrations.RenameField(
            model_name='request',
            old_name='DatePulled',
            new_name='date_pulled',
        ),
        migrations.RenameField(
            model_name='request',
            old_name='DateTwoEye',
            new_name='date_twoeye',
        ),
        migrations.RenameField(
            model_name='request',
            old_name='DiscNumber',
            new_name='disc_number',
        ),
        migrations.RenameField(
            model_name='request',
            old_name='Emails',
            new_name='emails',
        ),
        migrations.RenameField(
            model_name='request',
            old_name='IsSubmitted',
            new_name='is_submitted',
        ),
        migrations.RenameField(
            model_name='request',
            old_name='Network',
            new_name='network',
        ),
        migrations.RenameField(
            model_name='request',
            old_name='Request_id',
            new_name='request_id',
        ),
        migrations.RenameField(
            model_name='request',
            old_name='User',
            new_name='user',
        ),
        migrations.RenameField(
            model_name='user',
            old_name='Email',
            new_name='email',
        ),
        migrations.RenameField(
            model_name='user',
            old_name='User_id',
            new_name='user_id',
        ),
        migrations.RemoveField(
            model_name='request',
            name='PullNumber',
        ),
        migrations.AddField(
            model_name='request',
            name='pull_number',
            field=models.IntegerField(default=None),
        ),
        migrations.AlterField(
            model_name='file',
            name='classification',
            field=models.OneToOneField(on_delete=django.db.models.deletion.DO_NOTHING, to='pages.Classification', to_field='Classification_id'),
        ),
        migrations.AlterField(
            model_name='request',
            name='network',
            field=models.OneToOneField(on_delete=django.db.models.deletion.DO_NOTHING, to='pages.Network', to_field='Network_id'),
        ),
        migrations.AlterField(
            model_name='request',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.DO_NOTHING, to='pages.User', to_field='User_id'),
        ),
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.OneToOneField(on_delete=django.db.models.deletion.DO_NOTHING, to='pages.Email', to_field='Email_id'),
        ),
    ]
