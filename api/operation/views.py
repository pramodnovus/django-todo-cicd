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
import logging
############################################### ADD MAN-DAYS FILLED BY OPERATION TEAM - BULK UPDATE  ##################################################

class ProjectUpdateBulkAPIView(APIView):
    serializer_class = ProjectUpdateSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=ProjectUpdateSerializer(many=True))
    def post(self, request):
        data = request.data
        if isinstance(data, dict):  # Single create
            return self.handle_create([data], request)
        elif isinstance(data, list):  # Bulk create
            return self.handle_create(data, request)
        else:
            return Response({"error": "Invalid data format"}, status=status.HTTP_400_BAD_REQUEST)

    def handle_create(self, data, request):
        serializer = ProjectUpdateSerializer(data=data, many=True, context={'request': request})
        if serializer.is_valid():
            try:
                self.perform_create(serializer)
                return Response({"message": "Operation teams created successfully"}, status=status.HTTP_201_CREATED)
            except ValueError as ve:
                return JsonResponse({'error': str(ve)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        for item in serializer.validated_data:
            ProjectUpdate.objects.create(**item)


class OperationTeamListView(APIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = ProjectPerDaySerializer

    @swagger_auto_schema(request_body=ProjectPerDaySerializer)
    def post(self, request, *args, **kwargs):
        serializer = ProjectPerDaySerializer(data=request.data)
        try:
            if serializer.is_valid():
                project_id = serializer.validated_data['project_id']
                print('@@@@@@@@@@@@@@@')
                if project_id:
                    operation_teams = ProjectUpdate.objects.filter(project_id=project_id).all()
                else:
                    operation_teams = ProjectUpdate.objects.all()
                serializer = OperationTeamSerializer(operation_teams, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
        except serializers.ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
