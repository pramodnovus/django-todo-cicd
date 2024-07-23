from django.contrib import admin
from .models import *
from import_export.admin import ImportExportModelAdmin

@admin.register(operationTeam)
class operationTeamAdmin(ImportExportModelAdmin):
    list_display = ('name','project_code','date','man_days','total_achievement','remaining_time','remaining_interview','reason_for_adjustment','status')



@admin.register(ProjectAssignment)
class ProjectAssignment(admin.ModelAdmin):
    list_display = ('project','assigned_by','assigned_to','assigned_at')