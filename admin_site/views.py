# admin_site/views.py
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from django.contrib.auth.models import User
from users.models import UserProfile, Class
from django.contrib import messages
from .forms import TeacherForm, StudentForm, ClassForm, TeacherSearchForm, StudentSearchForm

from django.db.models import Avg, Count
from datetime import datetime, timedelta


def is_admin(user):
    """检查用户是否为管理员"""
    return user.is_authenticated and hasattr(user, 'userprofile') \
        and user.userprofile.role == 'admin'


@login_required
@user_passes_test(is_admin)
def dashboard(request):
    """管理员仪表板视图"""
    context = {
        'teacher_count': UserProfile.objects.filter(role='teacher').count(),
        'student_count': UserProfile.objects.filter(role='student').count(),
    }
    return render(request, 'admin_site/dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def teacher_list(request):
    """教师列表视图"""
    form = TeacherSearchForm(request.GET)
    teachers = UserProfile.objects.select_related('user').filter(role='teacher')

    if form.is_valid() and form.cleaned_data['search_term']:
        search_term = form.cleaned_data['search_term']
        teachers = teachers.filter(
            Q(user__username__icontains=search_term) |
            Q(user__first_name__icontains=search_term) |
            Q(user__last_name__icontains=search_term) |
            Q(user__email__icontains=search_term)
        )

    return render(request, 'admin_site/teacher_list.html', {
        'teachers': teachers,
        'form': form
    })


@login_required
@user_passes_test(is_admin)
def teacher_create(request):
    """创建教师视图"""
    if request.method == 'POST':
        form = TeacherForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            try:
                user = User.objects.create_user(
                    username=data['username'],
                    email=data['email'],
                    password=data['password'],
                    first_name=data['first_name'],
                    last_name=data['last_name']
                )
                UserProfile.objects.create(
                    user=user,
                    phone=data['phone'],
                    gender=data['gender'],
                    role='teacher'
                )
                messages.success(request, '教师创建成功')
                return redirect('admin_site:teacher_list')
            except Exception as e:
                messages.error(request, f'创建失败：{str(e)}')
    else:
        form = TeacherForm()

    return render(request, 'admin_site/teacher_form.html', {
        'form': form,
        'title': '添加教师'
    })


@login_required
@user_passes_test(is_admin)
def teacher_delete(request, pk):
    """删除教师视图"""
    teacher_profile = get_object_or_404(UserProfile, pk=pk, role='teacher')
    try:
        teacher_profile.user.delete()  # 级联删除用户档案
        messages.success(request, '教师删除成功')
    except Exception as e:
        messages.error(request, f'删除失败：{str(e)}')
    return redirect('admin_site:teacher_list')


@login_required
@user_passes_test(is_admin)
def teacher_edit(request, pk):
    """编辑教师视图"""
    teacher_profile = get_object_or_404(UserProfile, pk=pk, role='teacher')
    teacher = teacher_profile.user

    if request.method == 'POST':
        form = TeacherForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            try:
                teacher.username = data['username']
                teacher.email = data['email']
                if data['password']:
                    teacher.set_password(data['password'])
                teacher.first_name = data['first_name']
                teacher.last_name = data['last_name']
                teacher.save()

                teacher_profile.phone = data['phone']
                teacher_profile.gender = data['gender']
                teacher_profile.save()

                messages.success(request, '教师信息更新成功')
                return redirect('admin_site:teacher_list')
            except Exception as e:
                messages.error(request, f'更新失败：{str(e)}')
    else:
        form = TeacherForm(initial={
            'username': teacher.username,
            'email': teacher.email,
            'first_name': teacher.first_name,
            'last_name': teacher.last_name,
            'phone': teacher_profile.phone,
            'gender': teacher_profile.gender
        })

    return render(request, 'admin_site/teacher_form.html', {
        'form': form,
        'title': '编辑教师信息'
    })


@login_required
@user_passes_test(is_admin)
def student_list(request):
    """学生列表视图"""
    form = StudentSearchForm(request.GET)
    students = UserProfile.objects.select_related('user', 'class_id').filter(
        role='student'
    )

    if form.is_valid():
        if form.cleaned_data['search_term']:
            search_term = form.cleaned_data['search_term']
            students = students.filter(
                Q(user__username__icontains=search_term) |
                Q(user__first_name__icontains=search_term) |
                Q(user__last_name__icontains=search_term) |
                Q(user__email__icontains=search_term)
            )

        if form.cleaned_data['class_id']:
            students = students.filter(class_id=form.cleaned_data['class_id'])

    return render(request, 'admin_site/student_list.html', {
        'students': students,
        'form': form
    })


@login_required
@user_passes_test(is_admin)
def student_delete(request, pk):
    """删除学生视图"""
    student_profile = get_object_or_404(UserProfile, pk=pk, role='student')
    try:
        student_profile.user.delete()  # 级联删除用户档案
        messages.success(request, '学生删除成功')
    except Exception as e:
        messages.error(request, f'删除失败：{str(e)}')
    return redirect('admin_site:student_list')


@login_required
@user_passes_test(is_admin)
def student_create(request):
    """Create student view"""
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            try:
                user = User.objects.create_user(
                    username=data['username'],
                    email=data['email'],
                    password=data['password'],
                    first_name=data['first_name'],
                    last_name=data['last_name']
                )
                UserProfile.objects.create(
                    user=user,
                    phone=data['phone'],
                    gender=data['gender'],
                    role='student',
                    class_id=data['class_id']
                )
                messages.success(request, '学生创建成功')
                return redirect('admin_site:student_list')
            except Exception as e:
                messages.error(request, f'创建失败：{str(e)}')
    else:
        form = StudentForm()

    return render(request, 'admin_site/student_form.html', {
        'form': form,
        'title': '添加学生'
    })


@login_required
@user_passes_test(is_admin)
def student_edit(request, pk):
    """Edit student view"""
    student_profile = get_object_or_404(UserProfile, pk=pk, role='student')
    student = student_profile.user

    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            try:
                student.username = data['username']
                student.email = data['email']
                if data['password']:
                    student.set_password(data['password'])
                student.first_name = data['first_name']
                student.last_name = data['last_name']
                student.save()

                student_profile.phone = data['phone']
                student_profile.gender = data['gender']
                student_profile.class_id = data['class_id']
                student_profile.save()

                messages.success(request, '学生信息更新成功')
                return redirect('admin_site:student_list')
            except Exception as e:
                messages.error(request, f'更新失败：{str(e)}')
    else:
        form = StudentForm(initial={
            'username': student.username,
            'email': student.email,
            'first_name': student.first_name,
            'last_name': student.last_name,
            'phone': student_profile.phone,
            'gender': student_profile.gender,
            'class_id': student_profile.class_id
        })

    return render(request, 'admin_site/student_form.html', {
        'form': form,
        'title': '编辑学生信息'
    })


@login_required
@user_passes_test(is_admin)
def class_list(request):
    """班级列表视图"""
    classes = Class.objects.all()

    if request.method == 'POST':
        form = ClassForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '班级创建成功')
            return redirect('admin_site:class_list')
    else:
        form = ClassForm()

    return render(request, 'admin_site/class_list.html', {
        'classes': classes,
        'form': form
    })


@login_required
@user_passes_test(is_admin)
def class_edit(request, pk):
    """编辑班级视图"""
    class_obj = get_object_or_404(Class, pk=pk)

    if request.method == 'POST':
        form = ClassForm(request.POST, instance=class_obj)
        if form.is_valid():
            form.save()
            messages.success(request, '班级信息更新成功')
            return redirect('admin_site:class_list')
    else:
        form = ClassForm(instance=class_obj)

    return render(request, 'admin_site/class_form.html', {
        'form': form,
        'title': '编辑班级'
    })


@login_required
@user_passes_test(is_admin)
def class_delete(request, pk):
    """删除班级视图"""
    class_obj = get_object_or_404(Class, pk=pk)
    try:
        class_obj.delete()
        messages.success(request, '班级删除成功')
    except Exception as e:
        messages.error(request, f'删除失败：{str(e)}')
    return redirect('admin_site:class_list')


@login_required
@user_passes_test(is_admin)
def grade_analysis(request):
    """成绩分析视图"""
    # 获取所有学科
    subjects = Subject.objects.all()
    selected_subject = request.GET.get('subject')
    time_range = request.GET.get('time_range', 'month')  # 默认查看近一个月

    # 构建时间范围过滤条件
    today = datetime.now()
    if time_range == 'week':
        start_date = today - timedelta(days=7)
    elif time_range == 'month':
        start_date = today - timedelta(days=30)
    elif time_range == 'year':
        start_date = today - timedelta(days=365)
    else:
        start_date = today - timedelta(days=30)

    # 获取成绩数据
    student_exams = StudentExam.objects.select_related(
        'exam_paper', 'student'
    ).filter(
        created_at__gte=start_date,
        exam_paper__subject_id=selected_subject
    ) if selected_subject else StudentExam.objects.none()

    # 计算统计数据
    stats = {
        'total_exams': student_exams.count(),
        'average_score': student_exams.aggregate(Avg('total_score'))['total_score__avg'],
        'class_averages': student_exams.values(
            'student__userprofile__class_id__name'
        ).annotate(
            avg_score=Avg('total_score')
        ).order_by('student__userprofile__class_id__name'),
        'score_distribution': student_exams.values('total_score').annotate(
            count=Count('id')
        ).order_by('total_score')
    }

    return render(request, 'admin_site/grade_analysis.html', {
        'subjects': subjects,
        'selected_subject': selected_subject,
        'time_range': time_range,
        'stats': stats
    })
