# Generated by Django 4.2.10 on 2024-07-12 09:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('operation', '0002_projectupdate_projectassignment'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='projectupdate',
            name='project',
        ),
        migrations.RemoveField(
            model_name='projectupdate',
            name='updated_by',
        ),
        migrations.DeleteModel(
            name='ProjectAssignment',
        ),
        migrations.DeleteModel(
            name='ProjectUpdate',
        ),
    ]
