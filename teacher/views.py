# teacher/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import TeacherLoginForm
from users.models import UserProfile


def teacher_login(request):
    """教师登录视图"""
    if request.method == 'POST':
        form = TeacherLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user and hasattr(user, 'userprofile'):
                if user.userprofile.role == 'teacher':
                    login(request, user)
                    return redirect('teacher:dashboard')
                messages.error(request, '您不是教师用户，无法登录教师系统')
            else:
                messages.error(request, '用户名或密码错误')
    else:
        form = TeacherLoginForm()

    return render(request, 'teacher/login.html', {'form': form})


@login_required
def teacher_dashboard(request):
    """教师仪表板视图"""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'teacher':
        messages.error(request, '您没有权限访问教师系统')
        return redirect('teacher:login')

    return render(request, 'teacher/dashboard.html')
