from django.urls import path
from . import views

app_name = 'teacher'

urlpatterns = [
    path('login/', views.teacher_login, name='login'),
    path('dashboard/', views.teacher_dashboard, name='dashboard'),
    # 题库管理
    path('questions/', views.question_list, name='question_list'),
    path('questions/create/', views.question_create, name='question_create'),
    path('questions/<int:pk>/edit/', views.question_edit, name='question_edit'),
    path('questions/<int:pk>/delete/', views.question_delete, name='question_delete'),
    # 试卷管理相关的URL
    path('exam/papers/', views.exam_paper_list, name='exam_paper_list'),
    path('exam/papers/create/', views.exam_paper_create, name='exam_paper_create'),
    path('exam/papers/<int:pk>/edit/', views.exam_paper_edit, name='exam_paper_edit'),
    path('exam/papers/<int:pk>/delete/', views.exam_paper_delete, name='exam_paper_delete'),
    path('exam/papers/<int:pk>/questions/', views.exam_paper_questions, name='exam_paper_questions'),
    path('exam/papers/<int:pk>/preview/', views.exam_paper_preview, name='exam_paper_preview'),
    # 科目
    path('subjects/', views.subject_list, name='subject_list'),
    path('subjects/create/', views.subject_create, name='subject_create'),
    path('subjects/<int:pk>/edit/', views.subject_edit, name='subject_edit'),
    path('subjects/<int:pk>/delete/', views.subject_delete, name='subject_delete'),
    # 班级
    path('classes/', views.class_list, name='class_list'),
    path('classes/create/', views.class_create, name='class_create'),
    # path('classes/<int:pk>/edit/', views.class_edit, name='class_edit'),
    path('classes/<int:pk>/delete/', views.class_delete, name='class_delete'),
    # 考试
    path('exams/', views.exam_list, name='exam_list'),  # 考试列表
    path('exams/<int:pk>/', views.exam_detail, name='exam_detail'),  # 考试详情
    path('exams/<int:exam_id>/grade/<int:student_id>/', views.exam_grade, name='exam_grade'),  # 评分界面
    path('exams/publish/<int:pk>/', views.exam_publish, name='exam_publish'),  # 发布考试
    path('exams/close/<int:pk>/', views.exam_close, name='exam_close'),  # 关闭考试
]
