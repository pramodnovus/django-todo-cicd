# Generated by Django 4.2.10 on 2024-07-30 13:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('operation', '0005_projectupdate_status_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='projectupdate',
            old_name='project',
            new_name='project_id',
        ),
        migrations.RemoveField(
            model_name='projectupdate',
            name='man_days_filled',
        ),
    ]
