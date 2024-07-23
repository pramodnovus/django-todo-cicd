from rest_framework import viewsets
from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics
from rest_framework import status
from .models import *
from .serializers import *
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions
from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from rest_framework.exceptions import NotFound
from django.utils.html import strip_tags
from django.template.loader import render_to_string
from django.template.defaultfilters import linebreaksbr
from rest_framework import viewsets, permissions, status
from django.core import signing
from django.shortcuts import render
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework.decorators import action
from django.db import transaction
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import NotFound
from django.http import HttpResponse, HttpResponseNotFound, Http404

############################################# USER ROLE AS MANAGER IN PROJECT VIEWS######################################

class UserRoleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer

    @action(detail=False, methods=['get'])
    def managers(self, request):
        manager_role_name = 'Manager'
        managers = UserRole.objects.filter(role__name=manager_role_name).filter(department__name='Operation')
        serializer = self.get_serializer(managers, many=True)
        return Response(serializer.data)

####################################################### Project API View #######################################################
class ProjectListAPIView(APIView):
    def get(self, request):
        try:
            projects = Project.objects.all()
            serializer = ProjectSerializer(projects, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, *args, **kwargs):
        print(f"Authenticated user: {request.user}")
        data = request.data.copy()
        print(data)

        # Ensure request contains a valid manager
        manager_id = data.get('project_manager')
        if not manager_id:
            return Response({"error": "Manager ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            manager = UserRole.objects.get(user__id=manager_id)
            print("manager", manager)
            
        except UserRole.DoesNotExist:
            return Response({"error": "Manager does not exist."}, status=status.HTTP_400_BAD_REQUEST)

        # Ensure request contains a valid project type
        project_type_id = data.get('project_type')
        print("project_type", project_type_id)
        if not project_type_id:
            return Response({"error": "Project Type ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            project_type = projectType.objects.get(id=project_type_id)
            print("project_type", project_type)
        except projectType.DoesNotExist:
            return Response({"error": "Project Type does not exist."}, status=status.HTTP_400_BAD_REQUEST)

        # Add the authenticated user to the data
        data['created_by'] = request.user.id
        data['assigned_to'] = manager.id
        data['project_type'] = project_type.id

        # Serialize and validate the data
        serializer = ProjectSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProjectDetailAPIView(APIView):
    def get_object(self, pk):
        try:
            return get_object_or_404(Project, pk=pk)
        except Http404:
            raise Http404("Project does not exist")
        except Exception as e:
            raise e
    
    def get(self, request, pk):
        try:
            project = self.get_object(pk)
            serializer = ProjectSerializer(project)
            return Response(serializer.data)
        except Http404 as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, pk):
        try:
            project = self.get_object(pk)
            serializer = ProjectSerializer(project, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Http404 as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, pk):
        try:
            project = self.get_object(pk)
            project.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Http404 as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProjectCustomActionAPIView(APIView):
    def get_object(self, pk):
        try:
            return get_object_or_404(Project, pk=pk)
        except Http404:
            raise Http404("Project does not exist")
        except Exception as e:
            raise e
    
    def post(self, request, pk):
        try:
            project = self.get_object(pk)
            # Perform custom action logic here
            return Response({"message": f"Custom action performed for project {pk}"}, status=status.HTTP_200_OK)
        except Http404 as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



############################################### CLIENT VIEWS #################################################################

# from cacheops import cached_as

class ClientPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class ClientViewSet(viewsets.ModelViewSet):
    serializer_class = ClientSerializer
    pagination_class = ClientPagination

    def get_queryset(self):
        queryset = Client.objects.all()
        name = self.request.query_params.get('name', None)
        if name is not None:
            queryset = queryset.filter(name__icontains=name)
        return queryset

    # @cached_as(Client.objects.all())
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def handle_exception(self, exc):
        if isinstance(exc, NotFound):
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return super().handle_exception(exc)


###################################### PROJECT TYPE views ###########################################################

class ProjectTypePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class ProjectTypeViewSet(viewsets.ModelViewSet):
    queryset = projectType.objects.all()
    serializer_class = ProjectTypeSerializer
    pagination_class = ProjectTypePagination

    def get_queryset(self):
        queryset = projectType.objects.all()
        name = self.request.query_params.get('name', None)
        if name is not None:
            queryset = queryset.filter(name__icontains=name)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def handle_exception(self, exc):
        if isinstance(exc, NotFound):
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return super().handle_exception(exc)
