# Generated by Django 4.2.10 on 2024-07-12 10:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0006_delete_feemaster'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectupdate',
            name='remaining_interview',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]