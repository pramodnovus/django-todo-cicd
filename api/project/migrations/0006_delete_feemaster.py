# Generated by Django 4.2.10 on 2024-07-12 09:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0005_delete_projectmanager_delete_salesowner'),
    ]

    operations = [
        migrations.DeleteModel(
            name='FeeMaster',
        ),
    ]