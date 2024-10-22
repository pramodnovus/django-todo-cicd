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
from django.db import transaction
from django.db.models.functions import Cast
from django.db.models import IntegerField, FloatField
from django.db.models import F, Value
import logging
from api.operation.models import *

@receiver(post_save, sender=Client)
def create_project_code(sender, instance, created, **kwargs):
    if created:  # Only execute when a new Client instance is created
        
        # Generate project code pattern using client instance ID prefix, client name, and a suffix in ascending order
        client_prefix = str(instance.pk).zfill(3)  # Pad client instance ID with leading zeros
        client_name_medium = instance.name[:3].lower()  # First three characters of client name in lowercase
        
        suffix = str(instance.pk + 1).zfill(3)  # Generate suffix in ascending order
        
        # Construct the project code using the pattern
        project_code = f"{client_prefix}{client_name_medium}{suffix}"
        
        # Update the Client instance with the generated project code
        instance.project_code = project_code
        instance.save()
        
        
@receiver(post_save, sender=Project)
def update_project_code(sender, instance, created, **kwargs):
    if created:
        try:
            # Ensure this operation is within a transaction
            with transaction.atomic():
                project_code = instance.clients.project_code
                new_project_code = project_code

                # Check if the project code exists in the Project table
                while Project.objects.filter(project_code=new_project_code).exists():
                    # Extract the last three digits of the project code
                    last_three_digits = int(new_project_code[-3:])
                    # Increment the last three digits by 1
                    new_suffix = last_three_digits + 1
                    # Form the new project code by replacing the last three digits
                    new_project_code = project_code[:-3] + str(new_suffix).zfill(3)

                # Update the project code and initial sample size
                Project.objects.filter(id=instance.id).update(project_code=new_project_code, initial_sample_size=instance.sample)
        except Exception as e:
            print(f'Error: {e}')
            
            
# Set up logging
logger = logging.getLogger(__name__)
updating_project_update = False

@receiver(post_save, sender=Project)
def update_related_fields(sender, instance, **kwargs):
    global updating_project_update
    if kwargs.get('raw', False) or updating_project_update:
        return

    updating_project_update = True

    try:
        project_update_objects = ProjectUpdate.objects.filter(project_id=instance.id)
        print(project_update_objects)

        if project_update_objects.exists():
            first_project_update = project_update_objects.first()

            if instance.sample:
                sample_increment = int(instance.sample) - (int(first_project_update.remaining_interview) + int(first_project_update.total_achievement))
                for project_update in project_update_objects:
                    project_update.remaining_interview = int(project_update.remaining_interview) + sample_increment
                    project_update.save(update_fields=['remaining_interview'])

            last_project_update = project_update_objects.last()
            instance.remaining_interview = int(last_project_update.remaining_interview)

            aggregation_result = project_update_objects.aggregate(
                total_man_days=Sum(Cast('total_man_days', FloatField())),
                total_achievement=Sum(Cast('total_achievement', IntegerField()))
            )
            instance.man_days = aggregation_result['total_man_days'] or 0
            instance.total_achievement = aggregation_result['total_achievement'] or 0

        instance.save(update_fields=['remaining_interview', 'total_man_days', 'total_achievement'])

    except Exception as e:
        logger.error(f"An error occurred while updating project update: {e}")

    finally:
        updating_project_update = False

@receiver(pre_save, sender=Project)
def update_project_update_end_date(sender, instance, **kwargs):
    try:
        # Check if this is an update and not a creation
        if instance.pk:
            old_instance = Project.objects.get(pk=instance.pk)
            print('old_instance', old_instance)

            # Check if the tentative_end_date has changed
            if old_instance.tentative_end_date != instance.tentative_end_date:
                # Calculate the difference in tentative_end_date
                date_difference = instance.tentative_end_date - old_instance.tentative_end_date
                print("date_difference", date_difference, type(date_difference))
                print("instance.tentative_end_date", instance.tentative_end_date)

                # Round or truncate the timedelta to avoid high precision
                date_difference = timedelta(days=date_difference.days, seconds=date_difference.seconds)
                print('##########3')

                # Update all related ProjectUpdate objects
                project_updates = ProjectUpdate.objects.filter(project_id=instance.id)
                for project_update in project_updates:
                    # Update remaining_time by adding the difference
                    if project_update.remaining_time is not None:
                        project_update.remaining_time += date_difference
                    else:
                        project_update.remaining_time = date_difference
                    project_update.save()
    except Project.DoesNotExist:
        pass  # If the project does not exist, it is being created, so no need to update ProjectUpdate here
