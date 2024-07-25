from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *


router = DefaultRouter()


urlpatterns = [
    # path('', include(router.urls)),
    path('projects/add/man-days/', ProjectUpdateBulkAPIView.as_view(), name='project-update-bulk'),
   

]
