from rest_framework import serializers
from .models import *
from datetime import datetime, date
from api.user.models import *
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
import logging


# Configure logger
logger = logging.getLogger(__name__)

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ('id', 'project_code', 'name','project_type', 'initial_sample_size','sample',
                  'clients','cpi','set_up_fee','transaction_fee', 'status', 
                  'other_cost','operation_select','finance_select','upload_document',
                  'tentative_start_date','tentative_end_date','estimated_time','man_days','total_achievement','remaining_interview','status',
                  'remark','assigned_to','created_by','send_email_manager','created_at', 'updated_at'
                  )
        
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['clients'] = {
            'id': instance.clients.id,
            'name': instance.clients.name,
        }if instance.clients else None
        data['project_type'] = {
            'id': instance.project_type.id,
            'name': instance.project_type.name
        }if instance.project_type else None

        # Include assigned_by and assigned_to_by
        assignment = ProjectAssignment.objects.filter(project_id=instance).first()
        if assignment:
            data['project_assigned_by_manager'] = assignment.assigned_by.id
            data['project_assigned_to_teamlead'] = assignment.assigned_to.id
        else:
            data['project_assigned_by_manager'] = ""
            data['project_assigned_to_teamlead'] = ""
            
            
        return data

    
    def create(self, validated_data):
        request = self.context.get('request')
        
        # Check if the request and user are available
        user_id = request.user.id
        user_role = UserRole.objects.get(user=user_id)
        if request and request.user:
            validated_data['created_by'] = user_role
        else:
            # Raise an error if the user is not available
            raise ValidationError("User is not authenticated or request context is missing.")
          # Create the assignment
        try:
            # Create and return the project instance
            return super().create(validated_data)
        except Exception as e:
            # Handle any other exceptions that may occur during object creation
            raise ValidationError(f"Error creating project: {str(e)}") 
    

        


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = [
            'id', 'name', 'email', 'contact_person_email', 'project_code', 'address',
            'city', 'country', 'phone_number', 'contact_person', 'client_purchase_order_no',
            'email_id_for_cc', 'additional_survey', 'total_survey_to_be_billed_to_client',
            'other_specific_billing_instruction', 'is_active', 'created_at', 'updated_at'
        ]

class ProjectTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = projectType
        fields = ['id', 'name', 'is_active']

    def validate_name(self, value):
        if not value:
            raise serializers.ValidationError("Name field cannot be empty.")
        return value

    def to_representation(self, instance):
        try:
            data = super().to_representation(instance)
        except Exception as e:
            raise serializers.ValidationError(f"Error serializing ProjectType: {str(e)}")
        return data


############################################### USER ROLE SERILIZER AS MANAGER SHOW INTO DROPDOWN #######################################



class UserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRole
        fields = ['id', 'user', 'role', 'department', 'reports_to']
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['user'] = {
            'id': instance.user.id,
            'name': instance.user.username,
            'email': instance.user.email
        }
        data['role'] = {
            'id': instance.role.id,
            'name': instance.role.name
        }
        
        data['user_role'] = {
            'id': instance.id,
            'name': instance.user.username
        }
        
        data['department'] = {
            'id': instance.department.id,
            'name': instance.department.name
        } if instance.department else None
        data['reports_to'] = {
            'id': instance.reports_to.id,
            'name': instance.reports_to.user.username
        } if instance.reports_to else None
        return data
        

############################################## USER SERIALIZERS MODIFICATION ###############################################################

#class UserRoleSerializers(serializers.ModelSerializer):
    #class Meta:
        #model = UserRole
        #fields = []  
        
    #def to_representation(self, instance):
        #representation = super().to_representation(instance)
        #representation['user_role'] = {
            #'id': instance.id,
            #'name': instance.user.username
        #}
        #return representation         
        
        
############################################ PROJECT ASSIGNMENT BY OPERATION MANAGER  TO OPERATION TL ############################################


#class ProjectAssignmentSerializer(serializers.ModelSerializer):
    #class Meta:
        #model = ProjectAssignment
        #fields = '__all__'
        
    #def to_representation(self, instance):
        #representation = super().to_representation(instance)
        #representation['project_assigned_by'] = {
            #'project_id': instance.project_id.id,
            #'id': instance.assigned_by.id,
            #'name': instance.assigned_by.user.username
        #}
        
        #representation['project_assigned_to'] = {
            #'project_id': instance.project_id.id,
            #'id': instance.assigned_to.id,
            #'name': instance.assigned_to.user.username
        #}
        #return representation


class ProjectAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectAssignment
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.pop('assigned_by', None)
        representation.pop('assigned_to', None)

        # Get the project ID
        project_id = instance.project_id.id

        # Fetch all assignments related to the project
        assignments = ProjectAssignment.objects.filter(project_id=instance.project_id)

        # Create a list of users assigned to the project
        assigned_users = [
            {
                'id': assignment.assigned_to.id,
                'name': assignment.assigned_to.user.username
            }
            for assignment in assignments
        ]

        representation['project_assigned_to'] = assigned_users

        # Show the user who made the assignment for this specific instance
        representation['project_assigned_by'] = {
            'project_id': project_id,
            'id': instance.assigned_by.id,
            'name': instance.assigned_by.user.username
        }

        return representation

class ProjectStatusSerializer(serializers.Serializer):
    project_id = serializers.IntegerField()
    status = serializers.CharField(max_length=255)




class ProjectUpdatedDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectUpdatedData
        fields = ['project_id', 'sample', 'tentative_end_date', 'reason_for_adjustment']
    
class ProjectEmailSerializer(serializers.ModelSerializer):
    project_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Project
        fields = ['project_id', 'sample', 'tentative_end_date', 'reason_for_adjustment']
