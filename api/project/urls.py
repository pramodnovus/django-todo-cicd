from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *


router = DefaultRouter()
router.register(r'clients', ClientViewSet, basename="clients")
router.register(r'project_type', ProjectTypeViewSet, basename="project_type")
router.register(r'userrole', UserRoleViewSet, basename="project-managers")

urlpatterns = [
    path('', include(router.urls)),
    path('projects/', ProjectListAPIView.as_view(), name='project-list'),
    path('projects/<int:pk>/', ProjectDetailAPIView.as_view(), name='project-detail'),
    path('projects/<int:pk>/custom_action/', ProjectCustomActionAPIView.as_view(), name='project-custom-action'),
    path('userrole/managers/<int:manager_id>/teamleads/', TeamLeadsUnderManagerView.as_view(), name='teamleads-under-manager'),
    path('project-assignments/', ProjectAssignmentAPIView.as_view(), name='project-assignment'),
    path('update-project-status/', UpdateProjectStatusAPIView.as_view(), name='update_project_status'),
    path('interview/samplesize/edit', ProjectEmailView.as_view(), name='edit_project_sample'),
    path('updated-data/<int:project_id>/', ProjectUpdatedDataView.as_view(), name='project-updated-data'),

]
