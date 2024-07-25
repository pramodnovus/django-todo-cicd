from django.shortcuts import render
from rest_framework import viewsets
# from .models import operationTeam
from .serializers import *
from rest_framework.response import Response
from rest_framework import viewsets, permissions, status
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView
from api.project.models import Project  
from rest_framework.decorators import api_view 
import datetime
from django.core import signing
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

############################################### ADD MAN-DAYS FILLED BY OPERATION TEAM - BULK UPDATE  ##################################################

class ProjectUpdateBulkAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(request_body=ProjectUpdateSerializer(many=True))
    def post(self, request, *args, **kwargs):
        data = request.data
        try:
            with transaction.atomic():
                for update_data in data:
                    project_update_serializer = ProjectUpdateSerializer(data=update_data, context={'request': request})
                    if project_update_serializer.is_valid():
                        project_update = project_update_serializer.save()

                        # Update Project fields
                        project = project_update.project
                        project.man_days = project_update.total_man_days
                        project.remaining_time = project_update.remaining_time
                        project.remaining_interview = project_update.remaining_interview
                        project.total_achievement = project_update.total_achievement
                        project.save()
                    else:
                        return Response(project_update_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            return Response({"message": "Projects and updates saved successfully"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(request_body=ProjectUpdateSerializer(many=True))
    def put(self, request, *args, **kwargs):
        data = request.data
        try:
            with transaction.atomic():
                for update_data in data:
                    update_id = update_data.get('id')
                    project_update = get_object_or_404(ProjectUpdate, id=update_id)
                    project_update_serializer = ProjectUpdateSerializer(project_update, data=update_data)
                    if project_update_serializer.is_valid():
                        project_update = project_update_serializer.save()
                        project_update.updated_by = request.user

                        # Update Project fields
                        project = project_update.project
                        project.man_days = project_update.total_man_days
                        project.remaining_time = project_update.remaining_time
                        project.remaining_interview = project_update.remaining_interview
                        project.total_achievement = project_update.total_achievement
                        project.save()
                    else:
                        return Response(project_update_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            return Response({"message": "Projects man-days filled successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

