# student/urls.py

from django.urls import path
from . import views

app_name = 'student'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('exam/<int:pk>/', views.exam_detail, name='exam_detail'),
    path('exam/<int:pk>/submit/', views.exam_submit, name='exam_submit'),
    path('exam/<int:pk>/auto_submit/', views.exam_auto_submit, name='exam_auto_submit'),
]
