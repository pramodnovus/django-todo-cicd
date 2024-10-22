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
from django.core.mail import send_mail,BadHeaderError
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
from api.operation.models import *

############################################# USER ROLE AS MANAGER IN PROJECT VIEWS######################################

class UserRoleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def managers(self, request):
        manager_role_name = ['Manager','Ass.Manager','Sr.Manager']
        managers = UserRole.objects.filter(role__name=manager_role_name).filter(department__name='Operation')
        serializer = self.get_serializer(managers, many=True)
        return Response(serializer.data)


################################################## TL Under Manager ############################################################

class TeamLeadsUnderManagerView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get_subordinates(self, manager_role):
        """Recursively fetch all subordinates of a given manager role."""
        subordinates = UserRole.objects.filter(reports_to=manager_role)
        all_subordinates = list(subordinates)

        for subordinate in subordinates:
            # Recursively fetch subordinates of each subordinate
            all_subordinates.extend(self.get_subordinates(subordinate))
        
        return all_subordinates
    
    def get(self, request, manager_id, format=None):
        try:
            print(manager_id,'manager manager id manager id id did')
            # Fetch the UserRole of the Manager
            manager_role = UserRole.objects.get(id=manager_id)

            # Check if the manager's role is 'Director'
            if manager_role.role.name == 'Director':
                # If the manager is a Director, get all Team Leads
                team_leads = UserRole.objects.filter(role__name__in=[role.name for role in Role.objects.all()],department__name='Operation')
                # unique_assignments = {assignment.project_id.id: assignment for assignment in assignments}.values()
            elif manager_role.role.name in [role.name for role in Role.objects.all()]:
                # If the manager is a Manager, get only the Team Leads reporting to this Manager
                team_leads = UserRole.objects.filter(
                    reports_to=manager_role,
                    role__name__in=[role.name for role in Role.objects.all()],
                    department__name='Operation'
                )
            else:
                return Response(
                    {'error': 'The specified user is neither a Manager nor a Director'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            all_subordinates = self.get_subordinates(manager_role)
            
            
            # Serialize the manager details
            manager_serializer = UserRoleSerializer(manager_role)

            # Serialize the user information of the Team Leads
            team_leads_serializer = UserRoleSerializer(team_leads, many=True)
            
            subordinates_serializer = UserRoleSerializer(all_subordinates, many=True)
            
            response_data = {
                'manager': manager_serializer.data,
                'team_leads': team_leads_serializer.data,
                'subordinates': subordinates_serializer.data 
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except UserRole.DoesNotExist:
            return Response(
                {'error': 'Manager not found'},
                status=status.HTTP_404_NOT_FOUND
            )






####################################################### Project API View #######################################################

class ProjectListAPIView(APIView):
    #authentication_classes = [JWTAuthentication]
    #permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            projects = Project.objects.all()
            serializer = ProjectSerializer(projects, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(request_body=ProjectSerializer) 
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
        user_id = request.user.id
        user_role_id = UserRole.objects.get(user=user_id).id
        data['created_by'] = user_role_id
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
    #authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.AllowAny,]
    #permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Client.objects.all()
        # name = self.request.query_params.get('name', None)
        # print('hello name',name)
        # if name is not None:
        #     queryset = queryset.filter(name__icontains=name)
        #     print('my name',queryset)
        return queryset

    # @cached_as(Client.objects.all())
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        # print('modify name',queryset)
        # page = self.paginate_queryset(queryset)
        # print('page to page',page)
        # if page is not None:
        #     serializer = self.get_serializer(page, many=True)
        #     return self.get_paginated_response(serializer.data)
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
            # Fetch all assignments and remove duplicates based on project_id
            assignments = ProjectAssignment.objects.all()
            unique_assignments = {assignment.project_id.id: assignment for assignment in assignments}.values()
            
            serializer = ProjectAssignmentSerializer(unique_assignments, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(request_body=ProjectAssignmentSerializer(many=True))
    def post(self, request, *args, **kwargs):
        data = request.data
        if isinstance(data, list):
            # Handle bulk creation
            return self.bulk_create(data)
        else:
            # Handle single creation
            return self.single_create(data)

    def single_create(self, data):
        try:
            with transaction.atomic():
                project_id = data.get('project_id')
                assigned_by_id = data.get('assigned_by')
                assigned_to_id = data.get('assigned_to')

                if not project_id or not assigned_by_id or not assigned_to_id:
                    return Response({"error": "Project ID, Assigned By ID, and Assigned To ID are required."}, status=status.HTTP_400_BAD_REQUEST)

                project = get_object_or_404(Project, id=project_id)
                assigned_by = get_object_or_404(UserRole, id=assigned_by_id)
                assigned_to = get_object_or_404(UserRole, id=assigned_to_id)

                assignment = ProjectAssignment(project_id=project, assigned_by=assigned_by, assigned_to=assigned_to)
                assignment.save()

                project.status = "To Be Started"
                project.save()

                serializer = ProjectAssignmentSerializer(assignment)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def bulk_create(self, data):
        try:
            assignments = []
            with transaction.atomic():
                for item in data:
                    project_id = item.get('project_id')
                    assigned_by_id = item.get('assigned_by')
                    assigned_to_id = item.get('assigned_to')

                    if not project_id or not assigned_by_id or not assigned_to_id:
                        return Response({"error": "Project ID, Assigned By ID, and Assigned To ID are required for all items."}, status=status.HTTP_400_BAD_REQUEST)

                    project = get_object_or_404(Project, id=project_id)
                    assigned_by = get_object_or_404(UserRole, id=assigned_by_id)
                    assigned_to = get_object_or_404(UserRole, id=assigned_to_id)

                    assignment = ProjectAssignment(project_id=project, assigned_by=assigned_by, assigned_to=assigned_to)
                    assignment.save()
                    assignments.append(assignment)

                    project.status = "To Be Started"
                    project.save()

                serializer = ProjectAssignmentSerializer(assignments, many=True)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UpdateProjectStatusAPIView(APIView):
    serializer_class = ProjectStatusSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=ProjectStatusSerializer)
    def post(self, request, *args, **kwargs):
        serializer = ProjectStatusSerializer(data=request.data)
        if serializer.is_valid():
            project_id = serializer.validated_data['project_id']
            status_value = serializer.validated_data['status']
            
            try:
                project = Project.objects.get(id=project_id)
                last_project_update = ProjectUpdate.objects.filter(project_id=project_id).last()
                
                if last_project_update:
                    last_project_update.status = status_value
                    last_project_update.save()
                
                project.status = status_value
                project.save()
                
                return Response({"message": "Project status updated successfully."}, status=status.HTTP_200_OK)
            except Project.DoesNotExist:
                return Response({"message": "Project with the given ID does not exist."}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class ProjectEmailView(APIView):
    serializer_class = ProjectEmailSerializer
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(request_body=ProjectEmailSerializer)
    def post(self, request):
        logger.info("Received request data: %s", request.data)
        serializer = ProjectEmailSerializer(data=request.data)

        if serializer.is_valid():
            project_id = serializer.validated_data['project_id']
            sample = serializer.validated_data.get('sample', '')
            tentative_end_date = serializer.validated_data.get('tentative_end_date', '')
            reason_for_adjustment = serializer.validated_data.get('reason_for_adjustment', '')
            user_role = UserRole.objects.get(user=request.user.id)


            try:
                project = get_object_or_404(Project, id=project_id)
            except Exception as e:
                logger.error("Error fetching project: %s", e)
                return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)

            manager_emails = "ankit.sharma@novusinsights.com"
            frm_email = "noreply.erp@unimrkt.com"

            subject = f"Project Update: {project.name}"
            message = f"""Dear Manager,

            Here is an update on the project:

            - **Project ID**: {project_id}
            - **Sample**: {sample}
            - **Tentative End Date**: {tentative_end_date}
            - **Reason for Adjustment**: {reason_for_adjustment}

            Please review the project details at your earliest convenience.
            """

            to_email = manager_emails

            try:
                send_mail(
                    subject,
                    message,
                    frm_email,
                    [to_email],
                )
                logger.info("Email sent successfully to: %s", to_email)
            except Exception as e:
                logger.error("Error sending email: %s", e)
                return Response({"error": f"Failed to send email.{e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            try:
                ProjectUpdatedData.objects.update_or_create(
                    project_id=project_id,
                    defaults={
                        'sample': sample,
                        'tentative_end_date': tentative_end_date,
                        'reason_for_adjustment': reason_for_adjustment,
                        'updated_by' : user_role,
                    }
                )
                project.send_email_manager = True
                project.save()
            except Exception as e:
                logger.error("Error updating project data: %s", e)
                return Response({"error": f"Failed to update project data.{e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            context = {
                "message": "Email sent successfully!",
                "project_id": project_id,
                "sample": sample,
                "tentative_end_date": tentative_end_date,
                "reason_for_adjustment": reason_for_adjustment
            }
            return Response(context, status=status.HTTP_200_OK)
        else:
            logger.error("Serializer errors: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProjectUpdatedDataView(APIView):
    def get(self, request, project_id):
        # Get the project based on project_id and check if send_email_manager is True
        project = get_object_or_404(Project, id=project_id, send_email_manager=True)

        # Filter data in ProjectUpdatedData based on project_id
        updated_data = ProjectUpdatedData.objects.filter(project_id=project_id)

        if updated_data.exists():
            serializer = ProjectUpdatedDataSerializer(updated_data, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"message": "No updated data found for this project ID."}, status=status.HTTP_404_NOT_FOUND)

