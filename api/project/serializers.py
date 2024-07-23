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
                  'tentative_start_date','tentative_end_date','estimated_time','status',
                  'remark','assigned_to','created_by','created_at', 'updated_at')
        
    
    def create(self, validated_data):
        request = self.context.get('request')

        # Check if the request and user are available
        if request and request.user:
            validated_data['created_by'] = request.user
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
from rest_framework import serializers
from api.user.models import UserRole

class UserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRole
        fields = ['id', 'user', 'role', 'department', 'reports_to']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['user'] = {
            'id': instance.user.id,
            'username': instance.user.username,
            'email': instance.user.email
        }
        data['role'] = {
            'id': instance.role.id,
            'name': instance.role.name
        }
        data['department'] = {
            'id': instance.department.id,
            'name': instance.department.name
        } if instance.department else None
        data['reports_to'] = {
            'id': instance.reports_to.id,
            'username': instance.reports_to.user.username
        } if instance.reports_to else None
        return data
        