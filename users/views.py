# users/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import UnifiedLoginForm, UserUpdateForm, ProfileUpdateForm


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


@login_required
def profile(request):
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, instance=request.user.userprofile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, '个人信息更新成功')
            return redirect('users:profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.userprofile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }

    # 根据用户角色返回对应的模板
    role = request.user.userprofile.role
    if role == 'admin':
        template_name = 'admin_site/profile.html'
    else:
        template_name = f'{role}/profile.html'
    return render(request, template_name, context)
