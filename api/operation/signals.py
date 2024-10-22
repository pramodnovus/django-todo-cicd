from django.db.models.signals import post_save,post_delete
from django.dispatch import receiver
from .models import *
from api.project.models import Project
from django.db.models import Sum
from datetime import timedelta
from django.db.models.functions import Cast
from django.db.models import IntegerField, FloatField
from django.db.models import F, Value
import logging


# Set up logging
logger = logging.getLogger(__name__)

# Global flags to control signal handling
updating_project = False

@receiver(post_save, sender=ProjectUpdate)
def update_project_instance(sender, instance, created, **kwargs):
    # if created:
        project_id = instance.project_id.id
        print('project_id', project_id)
        update_project(project_id)

def update_project(project_id):
    global updating_project
    updating_project = True

    try:
        project_instance = Project.objects.filter(id=project_id).first()
        if not project_instance:
            logger.error(f"Project with id {project_id} not found.")
            return

        aggregation_result = ProjectUpdate.objects.filter(project_id=project_id).aggregate(
            total_man_days=Sum(Cast('total_man_days', FloatField())),
            total_achievement=Sum(Cast('total_achievement', IntegerField()))
        )
        total_man_days = aggregation_result['total_man_days'] or 0
        total_achievement = aggregation_result['total_achievement'] or 0
        print(total_man_days, total_achievement)
        project_instance.man_days = total_man_days
        project_instance.total_achievement = total_achievement

        last_operation_team = ProjectUpdate.objects.filter(project_id=project_id).last()
        print(last_operation_team)
        print('last to last', last_operation_team.remaining_interview if last_operation_team else None)

        if last_operation_team:
            remaining_interview = last_operation_team.remaining_interview
            if remaining_interview is None:
                remaining_interview = 0  # Handle the case where remaining_interview is None

            remaining_interview = int(remaining_interview)
            if remaining_interview < 0:
                project_instance.status = 'Completed'
                logger.error("Interviews completed. Cannot create another entry.")
                raise ValueError("Interviews completed. Cannot create another entry.")
            else:
                project_instance.remaining_interview = remaining_interview
                project_instance.remaining_time = last_operation_team.remaining_time
                project_instance.status = last_operation_team.status

                if remaining_interview == 0:
                    project_instance.status = 'Completed'

        project_instance.save()

    except Exception as e:
        logger.error(f"An error occurred while updating project: {e}")
        raise
    finally:
        updating_project = False


    



    
