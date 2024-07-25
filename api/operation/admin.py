from django.contrib import admin
from .models import *
from import_export.admin import ImportExportModelAdmin

class ProjectUpdateAdmin(admin.ModelAdmin):
    list_display = (
        'project',
        'updated_by',
        'update_date',
        'man_days_filled',
        'total_man_days',
        'remaining_time',
        'remaining_interview',
        'total_achievement',
        'is_active',
    )
    list_filter = (
        'update_date',
        'project',
        'updated_by',
        'is_active',
    )
    search_fields = (
        'project__name',
        'updated_by__user__username',
        'remaining_interview',
        'total_achievement',
    )
    ordering = ('-update_date',)
    readonly_fields = ('update_date',)  # Assuming you don't want this field to be edited

admin.site.register(ProjectUpdate, ProjectUpdateAdmin)


@admin.register(ProjectAssignment)
class ProjectAssignment(admin.ModelAdmin):
    list_display = ('project','assigned_by','assigned_to','assigned_at')