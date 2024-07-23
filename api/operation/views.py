from django.shortcuts import render
from rest_framework import viewsets
from .models import operationTeam
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

