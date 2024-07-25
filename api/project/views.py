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
from api.user.serializers import *

############################################# USER ROLE AS MANAGER IN PROJECT VIEWS######################################

class UserRoleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def managers(self, request):
        manager_role_name = 'Manager'
        managers = UserRole.objects.filter(role__name=manager_role_name).filter(department__name='Operation')
        serializer = self.get_serializer(managers, many=True)
        return Response(serializer.data)


################################################## TL Under Manager ############################################################

class TeamLeadsUnderManagerView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request, manager_id, format=None):
        try:
            # Fetch the UserRole of the Operations Manager
            manager_role = UserRole.objects.get(id=manager_id)
            
            # Ensure the role of the manager is 'Operations Manager'
            if manager_role.role.name != 'Manager':
                return Response(
                    {'error': 'The specified user is not an Operations Manager'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get all Team Leads reporting to this Operations Manager
            team_leads = UserRole.objects.filter(
                reports_to=manager_role,
                role__name='Team Lead'
            )

            # Serialize the manager details
            manager_serializer = UserRoleSerializers(manager_role.user)

            # Serialize the user information of the Team Leads
            team_leads_serializer = UserRoleSerializers([lead.user for lead in team_leads], many=True)

            response_data = {
                'manager': manager_serializer.data,
                'team_leads': team_leads_serializer.data
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        except UserRole.DoesNotExist:
            return Response(
                {'error': 'Operations Manager not found'},
                status=status.HTTP_404_NOT_FOUND
            )



####################################################### Project API View #######################################################

class ProjectListAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
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
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
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


    def patch(self, request, pk):
        try:
            project = self.get_object(pk)
            data = request.data

            # Only allow updates to man_days or tentative_end_date
            partial_data = {}
            if 'man_days' in data:
                partial_data['man_days'] = data['man_days']
            if 'tentative_end_date' in data:
                partial_data['tentative_end_date'] = data['tentative_end_date']

            serializer = ProjectSerializer(project, data=partial_data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Http404 as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)        
        

class ProjectCustomActionAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
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
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

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
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

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

############################################ PROJECT ASSIGNMENT BY OPERATION MANAGER  TO OPERATION TL ############################################

@swagger_auto_schema(request_body=ProjectAssignmentSerializer(many=True))
class ProjectAssignmentAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            assignments = ProjectAssignment.objects.all()
            serializer = ProjectAssignmentSerializer(assignments, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
    # POST request to create a new project assignment
    def post(self, request, *args, **kwargs):
        data = request.data

        if isinstance(data, list):
            # Handle bulk creation
            return self.bulk_create(data)
        else:
            # Handle single creation
            return self.single_create(data)
        
        
    # Helper function to handle bulk creation
    def single_create(self, data):
        try:
            with transaction.atomic():
                project_id = data.get('project')
                assigned_by_id = data.get('assigned_by')
                assigned_to_id = data.get('assigned_to')

                if not project_id or not assigned_by_id or not assigned_to_id:
                    return Response({"error": "Project ID, Assigned By ID, and Assigned To ID are required."}, status=status.HTTP_400_BAD_REQUEST)

                project = get_object_or_404(Project, id=project_id)
                assigned_by = get_object_or_404(UserRole, id=assigned_by_id)
                assigned_to = get_object_or_404(UserRole, id=assigned_to_id)

                assignment = ProjectAssignment(project=project, assigned_by=assigned_by, assigned_to=assigned_to)
                assignment.save()

                serializer = ProjectAssignmentSerializer(assignment)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    # Helper function to handle bulk creation
    def bulk_create(self, data):
        try:
            assignments = []
            with transaction.atomic():
                for item in data:
                    project_id = item.get('project')
                    assigned_by_id = item.get('assigned_by')
                    assigned_to_id = item.get('assigned_to')

                    if not project_id or not assigned_by_id or not assigned_to_id:
                        return Response({"error": "Project ID, Assigned By ID, and Assigned To ID are required for all items."}, status=status.HTTP_400_BAD_REQUEST)

                    project = get_object_or_404(Project, id=project_id)
                    assigned_by = get_object_or_404(UserRole, id=assigned_by_id)
                    assigned_to = get_object_or_404(UserRole, id=assigned_to_id)

                    assignment = ProjectAssignment(project=project, assigned_by=assigned_by, assigned_to=assigned_to)
                    assignments.append(assignment)

                ProjectAssignment.objects.bulk_create(assignments)

                serializer = ProjectAssignmentSerializer(assignments, many=True)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
