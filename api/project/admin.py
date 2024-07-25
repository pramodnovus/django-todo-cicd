from django.contrib import admin
from .models import *
from import_export.admin import ImportExportModelAdmin


@admin.register(projectType)
class ProjectTypeAdmin(ImportExportModelAdmin):
    list_display = ['id', 'name'] 
    list_display_links = ['id', 'name'] 

    class Meta:
        model = projectType

@admin.register(Project)
class ProjectAdmin(ImportExportModelAdmin):
    list_display = ['id','project_code','name','project_type','sample','clients','cpi','other_cost','operation_select','finance_select','upload_document','tentative_start_date','tentative_end_date','estimated_time','status','remark','assigned_to'] 

# @admin.register(ProjectCode)
# class ProjectCodeAdmin(ImportExportModelAdmin):
#     list_display = ('project_code',)
    
    
@admin.register(Client)
class ClientAdmin(ImportExportModelAdmin):
    list_display = ('name','project_code','client_purchase_order_no','email_id_for_cc','additional_survey','total_survey_to_be_billed_to_client','other_specific_billing_instruction')
    


