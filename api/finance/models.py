from django.db import models
from api.user.models import *
from api.project.models import Project



class FinanceRequest(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True)
    requested_by = models.ForeignKey(UserRole, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ], default='Pending')
    request_date = models.DateTimeField(auto_now_add=True)

    # def __str__(self):
    #     return f"Finance request for {self.project.name} by {self.requested_by.user.username}"
     
