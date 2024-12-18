from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from users.models import Class, UserProfile
from .forms import TeacherLoginForm, QuestionForm, TeacherClassForm, SubjectForm

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import ExamPaperForm, QuestionSelectionForm
from teacher.models import ExamPaper, ExamQuestion, TeacherClass, Question, Subject


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

    # 获取试卷统计数据
    exam_papers = ExamPaper.objects.filter(created_by=request.user)
    exam_papers_count = exam_papers.count()
    draft_papers_count = exam_papers.filter(status='draft').count()
    published_papers_count = exam_papers.filter(status='published').count()
    ended_papers_count = exam_papers.filter(status='ended').count()

    # 获取最近的试卷
    recent_papers = exam_papers.select_related('subject').order_by('-created_at')[:5]

    # 获取教师的班级和学生统计
    teacher_classes = TeacherClass.objects.filter(teacher=request.user)
    classes_count = teacher_classes.values('class_id').distinct().count()

    # 获取这些班级的学生数量
    class_ids = teacher_classes.values_list('class_id', flat=True)
    students_count = UserProfile.objects.filter(
        role='student',
        class_id__in=class_ids
    ).count()

    # 获取考试统计
    now = timezone.now()
    ongoing_exams_count = exam_papers.filter(
        status='published',
        start_time__lte=now,
        end_time__gte=now
    ).count()

    # 获取待批改试卷数量
    # pending_grading_count = StudentExam.objects.filter(
    #     exam_paper__created_by=request.user,
    #     exam_paper__status='ended',
    #     total_score__isnull=True
    # ).count()

    context = {
        'exam_papers_count': exam_papers_count,
        'draft_papers_count': draft_papers_count,
        'published_papers_count': published_papers_count,
        'ended_papers_count': ended_papers_count,
        'classes_count': classes_count,
        'students_count': students_count,
        'ongoing_exams_count': ongoing_exams_count,
        # 'pending_grading_count': pending_grading_count,
        'recent_papers': recent_papers,
    }

    return render(request, 'teacher/dashboard.html', context)


@login_required
def exam_paper_list(request):
    """试卷列表视图"""
    exam_papers = ExamPaper.objects.filter(created_by=request.user).select_related('subject')
    return render(request, 'teacher/exam_paper_list.html', {'exam_papers': exam_papers})


@login_required
def exam_paper_create(request):
    """创建试卷视图"""
    if request.method == 'POST':
        form = ExamPaperForm(request.POST)
        if form.is_valid():
            exam_paper = form.save(commit=False)
            exam_paper.created_by = request.user
            exam_paper.status = 'draft'
            exam_paper.save()
            messages.success(request, '试卷创建成功')
            return redirect('teacher:exam_paper_questions', pk=exam_paper.pk)
    else:
        form = ExamPaperForm()

    return render(request, 'teacher/exam_paper_form.html', {
        'form': form,
        'title': '创建试卷'
    })


@login_required
def exam_paper_edit(request, pk):
    """编辑试卷视图"""
    exam_paper = get_object_or_404(ExamPaper, pk=pk, created_by=request.user)

    if request.method == 'POST':
        form = ExamPaperForm(request.POST, instance=exam_paper)
        if form.is_valid():
            form.save()
            messages.success(request, '试卷更新成功')
            return redirect('teacher:exam_paper_list')
    else:
        form = ExamPaperForm(instance=exam_paper)

    return render(request, 'teacher/exam_paper_form.html', {
        'form': form,
        'title': '编辑试卷'
    })


@login_required
def exam_paper_delete(request, pk):
    """删除试卷视图"""
    exam_paper = get_object_or_404(ExamPaper, pk=pk, created_by=request.user)
    exam_paper.delete()
    messages.success(request, '试卷删除成功')
    return redirect('teacher:exam_paper_list')


@login_required
def exam_paper_questions(request, pk):
    """管理试卷试题视图"""
    exam_paper = get_object_or_404(ExamPaper, pk=pk, created_by=request.user)

    if request.method == 'POST':
        # 获取选中的试题ID列表
        selected_question_ids = request.POST.getlist('questions')

        try:
            with transaction.atomic():
                # 清除当前试卷的所有试题
                ExamQuestion.objects.filter(exam_paper=exam_paper).delete()

                # 添加选中的试题
                total_score = 0
                for question_id in selected_question_ids:
                    # 获取分值
                    score = request.POST.get(f'score_{question_id}')
                    if not score:
                        raise ValueError(f'试题 {question_id} 未设置分值')

                    score = int(score)
                    if score <= 0:
                        raise ValueError(f'试题分值必须大于0')

                    # 创建试卷试题关联
                    ExamQuestion.objects.create(
                        exam_paper=exam_paper,
                        question_id=question_id,
                        score=score
                    )
                    total_score += score

                # 更新试卷总分和题目数量
                exam_paper.total_score = total_score
                exam_paper.question_count = len(selected_question_ids)
                exam_paper.save()

                messages.success(request, '试题保存成功！')
                return redirect('teacher:exam_paper_preview', pk=exam_paper.pk)

        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'保存失败：{str(e)}')

        # 如果保存失败，重定向回当前页面
        return redirect('teacher:exam_paper_questions', pk=pk)

    # GET 请求处理
    current_questions = exam_paper.examquestion_set.select_related('question').all()

    available_questions = Question.objects.filter(
        subject=exam_paper.subject,
        created_by=request.user
    ).exclude(
        id__in=[eq.question_id for eq in current_questions]
    )

    # 添加快速创建试题的表单
    if request.GET.get('add_question'):
        question_form = QuestionForm(initial={'subject': exam_paper.subject})
    else:
        question_form = None

    context = {
        'exam_paper': exam_paper,
        'current_questions': current_questions,
        'available_questions': available_questions,
        'question_form': question_form
    }

    return render(request, 'teacher/exam_paper_questions.html', context)


@login_required
def exam_paper_preview(request, pk):
    """试卷预览视图"""
    exam_paper = get_object_or_404(ExamPaper, pk=pk, created_by=request.user)

    # 获取所有试题并按类型分组
    exam_questions = exam_paper.examquestion_set.select_related('question').all()

    # 按题型分组
    questions_by_type = {}
    for exam_question in exam_questions:
        question_type = exam_question.question.get_type_display()
        if question_type not in questions_by_type:
            questions_by_type[question_type] = []
        questions_by_type[question_type].append(exam_question)

    context = {
        'exam_paper': exam_paper,
        'questions_by_type': questions_by_type,
        'total_score': sum(eq.score for eq in exam_questions),
        'question_count': len(exam_questions)
    }
    return render(request, 'teacher/exam_paper_preview.html', context)


@login_required
def question_list(request):
    """题库列表视图"""
    # 获取筛选参数
    subject_id = request.GET.get('subject')
    question_type = request.GET.get('type')
    search_term = request.GET.get('search')

    # 基础查询集
    questions = Question.objects.filter(created_by=request.user)

    # 应用筛选条件
    if subject_id:
        questions = questions.filter(subject_id=subject_id)
    if question_type:
        questions = questions.filter(type=question_type)
    if search_term:
        questions = questions.filter(
            Q(content__icontains=search_term) |
            Q(correct_answer__icontains=search_term)
        )

    # 获取科目列表供筛选用
    subjects = Subject.objects.all()
    question_types = Question.QUESTION_TYPES

    context = {
        'questions': questions.select_related('subject').order_by('-created_at'),
        'subjects': subjects,
        'question_types': question_types,
        'current_subject': subject_id,
        'current_type': question_type,
        'search_term': search_term
    }
    return render(request, 'teacher/question_list.html', context)


@login_required
def question_create(request):
    """创建试题视图"""
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.created_by = request.user
            question.save()

            messages.success(request, '试题创建成功！')

            # 处理返回地址
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url and next_url == 'exam_paper_questions':
                exam_paper_id = request.GET.get('exam_paper_id')
                if exam_paper_id:
                    return redirect('teacher:exam_paper_questions', pk=exam_paper_id)

            return redirect('teacher:question_list')
    else:
        initial = {}
        if 'subject' in request.GET:
            initial['subject'] = request.GET.get('subject')
        form = QuestionForm(initial=initial)

    context = {
        'form': form,
        'title': '创建试题'
    }
    if request.GET.get('exam_paper_id'):
        context['exam_paper_id'] = request.GET.get('exam_paper_id')

    return render(request, 'teacher/question_form.html', context)


@login_required
def question_edit(request, pk):
    """编辑试题视图"""
    question = get_object_or_404(Question, pk=pk, created_by=request.user)

    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            messages.success(request, '试题更新成功！')
            return redirect('teacher:question_list')
    else:
        form = QuestionForm(instance=question)

    return render(request, 'teacher/question_form.html', {
        'form': form,
        'title': '编辑试题'
    })


@login_required
def question_delete(request, pk):
    """删除试题视图"""
    question = get_object_or_404(Question, pk=pk, created_by=request.user)
    try:
        question.delete()
        messages.success(request, '试题删除成功！')
    except Exception as e:
        messages.error(request, f'删除失败：{str(e)}')
    return redirect('teacher:question_list')


@login_required
def subject_list(request):
    """科目列表视图"""
    subjects = Subject.objects.all()
    return render(request, 'teacher/subject_list.html', {'subjects': subjects})


@login_required
def subject_create(request):
    """创建科目视图"""
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '科目创建成功！')
            return redirect('teacher:subject_list')
    else:
        form = SubjectForm()

    return render(request, 'teacher/subject_form.html', {
        'form': form,
        'title': '创建科目'
    })


@login_required
def subject_edit(request, pk):
    """编辑科目视图"""
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            messages.success(request, '科目更新成功！')
            return redirect('teacher:subject_list')
    else:
        form = SubjectForm(instance=subject)

    return render(request, 'teacher/subject_form.html', {
        'form': form,
        'title': '编辑科目'
    })


@login_required
def class_list(request):
    """班级列表视图"""
    teacher_classes = TeacherClass.objects.filter(teacher=request.user).select_related(
        'class_id', 'subject'
    )
    context = {
        'teacher_classes': teacher_classes,
        'available_classes': Class.objects.all(),
        'available_subjects': Subject.objects.all()
    }
    return render(request, 'teacher/class_list.html', context)


@login_required
def class_create(request):
    """创建教师班级关联视图"""
    if request.method == 'POST':
        form = TeacherClassForm(request.POST)
        if form.is_valid():
            teacher_class = form.save(commit=False)
            teacher_class.teacher = request.user
            teacher_class.save()
            messages.success(request, '班级添加成功！')
            return redirect('teacher:class_list')
    else:
        form = TeacherClassForm()

    return render(request, 'teacher/class_form.html', {
        'form': form,
        'title': '添加班级'
    })


@login_required
def class_delete(request, pk):
    """删除教师班级关联视图"""
    teacher_class = get_object_or_404(TeacherClass, pk=pk, teacher=request.user)
    teacher_class.delete()
    messages.success(request, '班级移除成功！')
    return redirect('teacher:class_list')


@login_required
def subject_delete(request, pk):
    """删除科目视图"""
    subject = get_object_or_404(Subject, pk=pk)
    try:
        # 检查是否有关联的试卷或试题
        if ExamPaper.objects.filter(subject=subject).exists():
            messages.error(request, '该科目下存在试卷，无法删除')
            return redirect('teacher:subject_list')

        if Question.objects.filter(subject=subject).exists():
            messages.error(request, '该科目下存在试题，无法删除')
            return redirect('teacher:subject_list')

        subject.delete()
        messages.success(request, '科目删除成功')
    except Exception as e:
        messages.error(request, f'删除失败：{str(e)}')

    return redirect('teacher:subject_list')


@login_required
def class_delete(request, pk):
    """删除教师班级关联视图"""
    teacher_class = get_object_or_404(TeacherClass, pk=pk, teacher=request.user)
    try:
        # 检查是否有正在进行的考试
        ongoing_exams = ExamPaper.objects.filter(
            status='published',
            end_time__gt=timezone.now(),
            subject=teacher_class.subject
        ).exists()

        if ongoing_exams:
            messages.error(request, '该班级有正在进行的考试，无法移除')
            return redirect('teacher:class_list')

        teacher_class.delete()
        messages.success(request, '班级移除成功')
    except Exception as e:
        messages.error(request, f'移除失败：{str(e)}')

    return redirect('teacher:class_list')
