from django.urls import path
from . import views

app_name = 'admin_site'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('teachers/', views.teacher_list, name='teacher_list'),
    path('teachers/create/', views.teacher_create, name='teacher_create'),
    path('teachers/<int:pk>/edit/', views.teacher_edit, name='teacher_edit'),
    path('students/', views.student_list, name='student_list'),
    path('students/create/', views.student_create, name='student_create'),
    path('students/<int:pk>/edit/', views.student_edit, name='student_edit'),
    path('classes/', views.class_list, name='class_list'),
    path('classes/<int:pk>/edit/', views.class_edit, name='class_edit'),
    path('classes/<int:pk>/delete/', views.class_delete, name='class_delete'),
    path('teachers/<int:pk>/delete/', views.teacher_delete, name='teacher_delete'),
    path('students/<int:pk>/delete/', views.student_delete, name='student_delete'),
    path('grades/analysis/', views.grade_analysis, name='grade_analysis'),
]
