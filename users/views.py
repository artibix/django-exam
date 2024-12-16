# users/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import UnifiedLoginForm


def unified_login(request):
    """统一登录视图"""
    if request.method == 'POST':
        form = UnifiedLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user and hasattr(user, 'userprofile'):
                login(request, user)

                # 根据用户角色重定向到相应的仪表板
                role = user.userprofile.role
                if role == 'admin':
                    return redirect('admin_site:dashboard')
                elif role == 'teacher':
                    return redirect('teacher:dashboard')
                elif role == 'student':
                    return redirect('student:dashboard')

            messages.error(request, '用户名或密码错误')
    else:
        form = UnifiedLoginForm()

    return render(request, 'users/unified_login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')