from django.db import models
from django.core.exceptions import ValidationError
from datetime import timedelta
from .choice import status_choice
from api.user.models import *
from api.project.models import *




class ProjectUpdate(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='updates')
    updated_by = models.ForeignKey(UserRole, on_delete=models.CASCADE)
    update_date = models.DateTimeField(auto_now_add=True)
    man_days_filled = models.FloatField()
    total_man_days = models.FloatField()
    remaining_time = models.DurationField(default=timedelta())
    remaining_interview = models.CharField(max_length=255, null=True, blank=True)
    total_achievement = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('Project Initiated', 'Project Initiated'),
        ('To Be Started', 'To Be Started'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('On Hold', 'On Hold'),
    ], default='To Be Started')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.project.name} - {self.updated_by.role} - {self.updated_by.user.username} - {self.update_date} - {self.man_days_filled} - {self.total_man_days} - {self.remaining_time} - {self.total_achievement}"

    
    def remaining_time_in_hours(self):
        return self.remaining_time.total_seconds()/3600
    
    
    def calculate_remaining_interview(self):
        if self.total_man_days and self.man_days_filled:
            remaining_interview = self.total_man_days - self.man_days_filled
            return remaining_interview
        else:
            return None
    
    