# Generated by Django 4.2.10 on 2024-07-19 09:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0008_delete_projectcode'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='status',
            field=models.CharField(choices=[('To be started', 'To be started'), ('In Progress', 'In Progress'), ('Completed', 'Completed'), ('Hold', 'Hold')], default='To be started', max_length=20),
        ),
    ]
