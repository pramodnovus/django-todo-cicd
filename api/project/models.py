from django.db import models
from api.user.models import CustomUser
from django.core.exceptions import ValidationError
from datetime import date , datetime
from datetime import timedelta
from api.user.models import *


# Create your models here.


# CustomProjectManager Table
class CustomProjectManager(models.Manager):
    def create(self, validated_data):
        # Perform custom validation here
        if validated_data['tentative_end_date'] < date.today():
            raise ValidationError("Tentative end date cannot be in the past.")
        
        if self.duration and self.duration.total_seconds() <= 0:
            raise ValidationError({'duration': ['Duration must be greater than 0.']})

        return super().create(validated_data)
    
    
    
# Client Master Table
class Client(models.Model):
    name = models.CharField(max_length=100, unique=True)
    email = models.CharField(max_length=100,null=True,blank=True)
    contact_person_email = models.CharField(max_length=100,null=True,blank=True)
    project_code = models.CharField(max_length=50,null=True,blank=True, unique=True)
    address = models.CharField(max_length=100,null=True,blank=True)
    city = models.CharField(max_length=100,null=True,blank=True)
    country = models.CharField(max_length=100,null=True,blank=True)
    phone_number = models.IntegerField(null=True,blank=True)
    contact_person = models.CharField(max_length=100,null=True,blank=True)
    client_purchase_order_no = models.CharField(max_length=100,null=True,blank=True)
    email_id_for_cc = models.CharField(max_length=100,null=True,blank=True)
    additional_survey = models.CharField(max_length=100,null=True,blank=True)
    total_survey_to_be_billed_to_client = models.CharField(max_length=100,null=True,blank=True)
    other_specific_billing_instruction = models.CharField(max_length=255,null=True,blank=True)
    is_active = models.BooleanField(default=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    
class projectType(models.Model):
    name = models.CharField(max_length=50, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


    
# Project/Sales model
class Project(models.Model):
    project_id = models.CharField(max_length=100, null=True, blank=True)
    project_code = models.CharField(max_length=255, null=True, blank=True, unique=True)
    name = models.CharField(max_length=250)
    project_type = models.ForeignKey(projectType, on_delete=models.CASCADE, null=True, blank=True)
    initial_sample_size = models.CharField(max_length=50, null=True, blank=True)
    sample = models.CharField(max_length=50, null=True, blank=True)
    clients = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, blank=True)
    cpi = models.CharField(max_length=50, null=True, blank=True)
    set_up_fee = models.IntegerField(null=True, blank=True)
    transaction_fee = models.IntegerField(null=True, blank=True)
    other_cost = models.CharField(max_length=50, null=True, blank=True)
    operation_select = models.BooleanField(default=False)
    finance_select = models.BooleanField(default=False)
    upload_document = models.FileField(upload_to="File Upload", null=True, blank=True)
    tentative_start_date = models.DateTimeField(null=True, blank=True)
    tentative_end_date = models.DateTimeField(null=True, blank=True)
    estimated_time = models.DurationField(null=True, blank=True)
    status = models.CharField(max_length=255, null=True, blank=True)
    remark = models.CharField(max_length=255, null=True, blank=True)
    man_days = models.FloatField(null=True, blank=True)
    reason_for_adjustment = models.TextField(null=True, blank=True, default=None)
    send_email_manager = models.BooleanField(default=False, blank=True)
    total_achievement = models.CharField(max_length=255, null=True, blank=True, default=None)
    remaining_time = models.DurationField(default=timedelta(), null=True, blank=True)
    remaining_interview = models.CharField(max_length=255, null=True, blank=True, default=None)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_projects')
    assigned_to = models.ForeignKey(UserRole, null=True, blank=True, on_delete=models.SET_NULL, related_name='assigned_projects')
    status = models.CharField(max_length=20, choices=[
        ('To be started', 'To be started'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('Hold', 'Hold'),
    ], default='To be started')
    is_active = models.BooleanField(default=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.tentative_start_date and self.tentative_end_date:
            self.estimated_time = self.tentative_end_date - self.tentative_start_date
        super().save(*args, **kwargs)
        if self.status == 'Completed':
            self.raise_cbr_to_finance()

    def raise_cbr_to_finance(self):
        # Logic to raise CBR to finance team
        FinanceRequest.objects.create(
            project=self,
            requested_by=self.assigned_to
        )


class ProjectAssignment(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    assigned_by = models.ForeignKey(UserRole, on_delete=models.CASCADE, related_name='assigned_projects_by')
    assigned_to = models.ForeignKey(UserRole, on_delete=models.CASCADE, related_name='assigned_projects_to')
    assigned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project.name} assigned to {self.assigned_to.user.username} by {self.assigned_by.user.username}"

class ProjectUpdate(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='updates')
    updated_by = models.ForeignKey(UserRole, on_delete=models.CASCADE)
    update_date = models.DateTimeField(auto_now_add=True)
    man_days_filled = models.FloatField()
    total_man_days = models.FloatField()
    remaining_time = models.DurationField(default=timedelta())
    remaining_interview = models.CharField(max_length=255, null=True, blank=True)
    total_achievement = models.CharField(max_length=255, null=True, blank=True, default='INPROGRESS')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.project.project_code} - {self.updated_by.role} - {self.updated_by.user.username} - {self.update_date} - {self.man_days_filled} - {self.total_man_days} - {self.remaining_time} - {self.total_achievement}"

    
    def remaining_time_in_hours(self):
        return self.remaining_time.total_seconds()/3600
    
    
    def calculate_remaining_interview(self):
        if self.total_man_days and self.man_days_filled:
            remaining_interview = self.total_man_days - self.man_days_filled
            return remaining_interview
        else:
            return None
    

class ProjectUpdatedData(models.Model):
    project_code = models.CharField(max_length=255, null=True, blank=True, unique=True)
    sample = models.CharField(max_length=50,null=True, blank=True)
    tentative_end_date = models.DateTimeField(null=True,blank=True)   
    reason_for_adjustment = models.TextField(null=True, blank=True,default=None)
    

    