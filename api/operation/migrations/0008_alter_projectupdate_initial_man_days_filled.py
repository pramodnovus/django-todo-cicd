# Generated by Django 4.2.10 on 2024-07-30 14:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('operation', '0007_projectupdate_initial_man_days_filled'),
    ]

    operations = [
        migrations.AlterField(
            model_name='projectupdate',
            name='initial_man_days_filled',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
