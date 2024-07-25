from rest_framework import serializers
from .models import *
class ProjectUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectUpdate
        fields = ['id', 'project', 'updated_by', 'update_date', 'man_days_filled', 'total_man_days', 'remaining_time', 'remaining_interview', 'total_achievement', 'is_active']
        read_only_fields = ['id', 'update_date', 'updated_by']

    def create(self, validated_data):
        request = self.context.get('request')
        print(request)
        if request is None:
            raise serializers.ValidationError("Request context is not available")
        
        user_role = UserRole.objects.get(user=request.user)
        validated_data['updated_by'] = user_role
        return super().create(validated_data)
