"""
URL configuration for Exam project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from users.views import unified_login

urlpatterns = [
    path('', unified_login, name='login'),  # Root URL for login
    path('users/', include('users.urls')),  # 将统一登录页面设为首页
    path('admin/', include('admin_site.urls')),
    path('teacher/', include('teacher.urls')),
    # path('student/', include('student.urls')),
]
