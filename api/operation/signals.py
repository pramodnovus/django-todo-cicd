from django.db.models.signals import post_save,post_delete
from django.dispatch import receiver
from .models import *
from api.project.models import Project
from django.db.models import Sum
from datetime import timedelta


@receiver(post_save, sender=ProjectUpdate)
def update_project_instance(sender, instance, created, **kwargs):
    if created:
        project_code = instance.project_code
        update_project(project_code)

def update_project(project_code):
    project_instance = Project.objects.filter(project_code=project_code).first()
    if project_instance.remark is not None:
        # Aggregate man_days and total_achievement
        aggregation_result = ProjectUpdate.objects.filter(project_code=project_code).aggregate(
            total_man_days=Sum('man_days'),
            total_achievement=Sum('total_achievement')
        )
        total_man_days = aggregation_result['total_man_days'] or 0
        print('total man days',total_man_days)
        total_achievement = aggregation_result['total_achievement'] or 0

        project_instance.man_days = total_man_days
        project_instance.total_achievement = total_achievement
       

        # Get the last operationTeam instance
        last_operation_team = ProjectUpdate.objects.filter(project_code=project_code).last()
        if last_operation_team:
            # If remaining_interview becomes zero, set project status to "completed"
            remaining_interview = int(last_operation_team.remaining_interview)
            if remaining_interview < 0:
                project_instance.status = 'completed'
                # Raise error if another entry is attempted to be created
                raise ValueError("Interviews completed. Cannot create another entry.")
           
            else:
                project_instance.remaining_interview = remaining_interview
                project_instance.remaining_time = last_operation_team.remaining_time
                project_instance.status = last_operation_team.status
                        
                if int(last_operation_team.remaining_interview) == 0:
                     project_instance.status = 'completed'
                    

        project_instance.save()



    