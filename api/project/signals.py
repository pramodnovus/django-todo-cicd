from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from api.project.tasks import update_estimated_time_task
from .models import *
from django.db import IntegrityError
from django.utils import timezone
from datetime import timedelta
from django.utils.timezone import now, timedelta
from django.db.models import Sum
from django.utils.text import slugify


# @receiver(post_save, sender=Client)
# def create_or_update_project_code(sender, instance, created, **kwargs):
#     if created:
#         client_id = 