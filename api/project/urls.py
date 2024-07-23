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

]