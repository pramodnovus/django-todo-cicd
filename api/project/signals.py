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

@receiver(pre_save, sender=Client)
def set_unique_project_code(sender, instance, *args, **kwargs):
    if not instance.project_code:
        initial = slugify(instance.name[:3]).upper()
        last_project_code = Client.objects.filter(project_code__contains=f"{initial}").order_by('-created_at').first()

        
        if last_project_code:
            last_code_parts = last_project_code.project_code.split('CLI')[0]
            last_code_num = int(last_code_parts[-3:])
            new_code_num = last_code_num
        else:
            client_code_num = Client.objects.count()

        project_code_prefix = str(new_code_num).zfill(2)
        client_code_suffix = str(client_code_num).zfill(2)
        
        instance.project_code = f"{project_code_prefix}{initial}{client_code_suffix}"
        
        
        
@receiver(post_save, sender=Client)
def create_or_update_project_code(sender, instance, created, **kwargs):
    if not created:
        initial = slugify(instance.name[:3]).upper()
        project_code_prefix = instance.project_code[:2]
        client_code_suffix = str(instance.id).zfill(2)
        
        new_project_code = f"{project_code_prefix}{initial}{client_code_suffix}" 
        current_project_code = Client.objects.filter(project_code=instance.project_code).first()
        if current_project_code and instance.project_code != new_project_code:
            current_project_code.project_code = new_project_code
            current_project_code.save()
            instance.project_code = new_project_code
            instance.save()
            


from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils.text import slugify
from .models import Client, Project

@receiver(pre_save, sender=Project)
def set_unique_project_code(sender, instance, *args, **kwargs):
    if not instance.project_code:
        client = instance.clients
        if client:
            initial = slugify(client.name[:3]).upper()
            last_project = Project.objects.filter(project_code__startswith=initial).order_by('-created_at').first()
            project_count = Project.objects.filter(clients=client).count()
            

            if last_project and last_project.project_code:
                last_code_num = int(last_project.project_code.split(initial)[-1])
                new_code_num = last_code_num + 1
            else:
                new_code_num = 1
                
            project_code_prefix = str(project_count).zfill(3)
            project_code_suffix = str(new_code_num).zfill(3)
            instance.project_code = f"{project_code_prefix}{initial}{project_code_suffix}"

@receiver(post_save, sender=Client)
def create_or_update_project_code(sender, instance, created, **kwargs):
    if not created:
        initial = slugify(instance.name[:3]).upper()
        related_projects = Project.objects.filter(clients=instance)

        for project in related_projects:
            project_code_prefix = project.project_code[:3]
            project_code_suffix = project.project_code[3:]
            new_project_code = f"{initial}{project_code_suffix}"
            
            if project.project_code != new_project_code:
                project.project_code = new_project_code
                project.save()
            