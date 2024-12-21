from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone

from users.models import Class, UserProfile
from .forms import TeacherLoginForm, QuestionForm, TeacherClassForm, SubjectForm, ExamForm, ExamClassesForm

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import ExamPaperForm, QuestionSelectionForm
from teacher.models import ExamPaper, ExamQuestion, TeacherClass, Question, Subject, StudentExam, StudentAnswer, Exam
from django.db.models import Count, Avg


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

    # 在数据模型中没有定义试卷的状态字段,因此不能按状态过滤
    # draft_papers_count = exam_papers.filter(status='draft').count()
    # published_papers_count = exam_papers.filter(status='published').count()
    # ended_papers_count = exam_papers.filter(status='ended').count()

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
    ongoing_exams_count = Exam.objects.filter(  # 使用 Exam 模型
        exam_paper__created_by=request.user,
        start_time__lte=now,
        end_time__gte=now,
        status='in_progress'  # 使用 Exam 模型的 status 字段
    ).count()

    # 获取待批改试卷数量
    pending_grading_count = StudentExam.objects.filter(
        exam__exam_paper__created_by=request.user,  # 通过 exam 关联 ExamPaper
        status='submitted'  # 使用 StudentExam 模型的 status 字段
    ).count()

    context = {
        'exam_papers_count': exam_papers_count,
        # 'draft_papers_count': draft_papers_count,
        # 'published_papers_count': published_papers_count,
        # 'ended_papers_count': ended_papers_count,
        'classes_count': classes_count,
        'students_count': students_count,
        'ongoing_exams_count': ongoing_exams_count,
        'pending_grading_count': pending_grading_count,
        'recent_papers': recent_papers,
    }

    return render(request, 'teacher/dashboard.html', context)


@login_required
def exam_paper_list(request):
    """试卷列表视图"""
    exam_papers = ExamPaper.objects.filter(created_by=request.user).select_related('subject')

    # 按模板和普通试卷分类
    template_papers = exam_papers.filter(is_template=True)
    normal_papers = exam_papers.filter(is_template=False)

    context = {
        'template_papers': template_papers,
        'normal_papers': normal_papers
    }
    return render(request, 'teacher/exam_paper_list.html', context)


@login_required
def exam_paper_create(request):
    """创建试卷视图"""
    # 支持从模板创建
    template_id = request.GET.get('template_id')
    template = None

    if template_id:
        template = get_object_or_404(ExamPaper, pk=template_id, created_by=request.user, is_template=True)

    if request.method == 'POST':
        form = ExamPaperForm(request.POST)
        if form.is_valid():
            exam_paper = form.save(commit=False)
            exam_paper.created_by = request.user
            exam_paper.save()

            # 如果是从模板创建，复制试题
            if template:
                for eq in template.examquestion_set.all():
                    ExamQuestion.objects.create(
                        exam_paper=exam_paper,
                        question=eq.question,
                        score=eq.score
                    )
                exam_paper.total_score = template.total_score
                exam_paper.question_count = template.question_count
                exam_paper.save()

            messages.success(request, '试卷创建成功')
            return redirect('teacher:exam_paper_questions', pk=exam_paper.pk)
    else:
        initial = {}
        if template:
            initial = {
                'name': f'{template.name} - 副本',
                'subject': template.subject,
            }
        form = ExamPaperForm(initial=initial)

    context = {
        'form': form,
        'title': '创建试卷',
        'template': template
    }
    return render(request, 'teacher/exam_paper_form.html', context)


@login_required
def create_exam_step1(request):
    """第一步：填写考试基本信息"""
    if request.method == 'POST':
        form = ExamForm(request.user, request.POST)
        if form.is_valid():
            exam = form.save(commit=False)
            exam.created_by = request.user
            exam.save()
            return redirect('teacher:create_exam_step2', exam_id=exam.id)
    else:
        form = ExamForm(request.user)

    return render(request, 'teacher/exam_form_step1.html', {
        'form': form,
        'title': '创建考试 - 基本信息'
    })


@login_required
def create_exam_step2(request, exam_id):
    """第二步：选择参与班级"""
    exam = get_object_or_404(Exam, id=exam_id, created_by=request.user)

    if request.method == 'POST':
        form = ExamClassesForm(request.user, exam.exam_paper, request.POST)
        if form.is_valid():
            with transaction.atomic():
                # 保存选中的班级
                exam.classes.set(form.cleaned_data['classes'])

                # 为所选班级的学生创建考试记录
                selected_classes = form.cleaned_data['classes']
                students = User.objects.filter(
                    userprofile__role='student',
                    userprofile__class_id__in=selected_classes
                )

                student_exams = [
                    StudentExam(
                        student=student,
                        exam=exam,
                        status='in_progress'
                    ) for student in students
                ]
                StudentExam.objects.bulk_create(student_exams)

                messages.success(request, '考试创建成功！')
                return redirect('teacher:exam_list')
    else:
        form = ExamClassesForm(request.user, exam.exam_paper)

    return render(request, 'teacher/exam_form_step2.html', {
        'form': form,
        'exam': exam,
        'title': '创建考试 - 选择班级'
    })


@login_required
def exam_detail(request, pk):
    """考试详情视图"""
    exam = get_object_or_404(Exam, pk=pk, created_by=request.user)
    exam.update_status()

    student_exams = StudentExam.objects.filter(exam=exam)
    pass_threshold = exam.exam_paper.total_score * 0.6

    class_stats = {}
    for class_obj in exam.classes.all():
        # 获取班级的学生考试记录
        class_exams = student_exams.filter(
            student__userprofile__class_id=class_obj
        )

        # 已提交人数改为根据提交时间判断
        submitted_exams = class_exams.filter(submitted_at__isnull=False)
        submitted_count = submitted_exams.count()

        # 已批改的试卷必须同时满足：已提交且有总分
        graded_exams = submitted_exams.filter(total_score__isnull=False)
        graded_count = graded_exams.count()

        # 计算平均分和及格人数
        stats = graded_exams.aggregate(
            average=Avg('total_score'),
            pass_count=Count(
                'id',
                filter=Q(total_score__gte=pass_threshold)
            )
        )

        # 计算及格率
        pass_rate = (
            (stats['pass_count'] / graded_count * 100)
            if graded_count > 0 else None
        )

        class_stats[class_obj] = {
            'total': class_exams.count(),
            'submitted': submitted_count,
            'graded': graded_count,
            'average': stats['average'],
            'pass_rate': pass_rate
        }

    context = {
        'exam': exam,
        'class_stats': class_stats,
        'student_exams': student_exams.select_related(
            'student__userprofile',
            'student__userprofile__class_id'
        ).order_by(
            'student__userprofile__class_id__name',
            'student__username'
        )
    }
    return render(request, 'teacher/exam_detail.html', context)


@login_required
def exam_start(request, pk):
    """开始考试"""
    exam = get_object_or_404(Exam, pk=pk, created_by=request.user)

    if exam.status == 'preparing':
        exam.status = 'in_progress'
        exam.save()
        messages.success(request, '考试已开始！')
    else:
        messages.error(request, '只有准备中的考试才能开始！')

    return redirect('teacher:exam_detail', pk=pk)


@login_required
def exam_end(request, pk):
    """结束考试"""
    exam = get_object_or_404(Exam, pk=pk, created_by=request.user)

    if exam.status == 'in_progress':
        # 更新考试状态
        exam.status = 'ended'
        exam.end_time = timezone.now()
        exam.save()

        # 自动提交所有未交卷的试卷
        unsubmitted_exams = StudentExam.objects.filter(
            exam=exam,
            status='in_progress'
        )
        for student_exam in unsubmitted_exams:
            student_exam.submit()

        messages.success(request, '考试已结束！所有未交卷的答卷已自动提交。')
    else:
        messages.error(request, '只有进行中的考试才能结束！')

    return redirect('teacher:exam_detail', pk=pk)


@login_required
def exam_paper_questions(request, pk):
    """管理试卷试题视图"""
    exam_paper = get_object_or_404(ExamPaper, pk=pk, created_by=request.user)

    # 检查试卷是否已被使用
    if Exam.objects.filter(exam_paper=exam_paper).exists():
        messages.warning(request, '此试卷已被使用，无法修改题目')
        return redirect('teacher:exam_paper_preview', pk=pk)

    if request.method == 'POST':
        selected_question_ids = request.POST.getlist('questions')

        try:
            with transaction.atomic():
                ExamQuestion.objects.filter(exam_paper=exam_paper).delete()

                total_score = 0
                for question_id in selected_question_ids:
                    score = request.POST.get(f'score_{question_id}')
                    if not score or int(score) <= 0:
                        raise ValueError('试题分值必须大于0')

                    ExamQuestion.objects.create(
                        exam_paper=exam_paper,
                        question_id=question_id,
                        score=int(score)
                    )
                    total_score += int(score)

                exam_paper.total_score = total_score
                exam_paper.question_count = len(selected_question_ids)
                exam_paper.save()

                messages.success(request, '试题保存成功！')
                return redirect('teacher:exam_paper_preview', pk=pk)

        except Exception as e:
            messages.error(request, f'保存失败：{str(e)}')

    current_questions = exam_paper.examquestion_set.select_related('question')
    available_questions = Question.objects.filter(
        subject=exam_paper.subject,
        created_by=request.user
    ).exclude(id__in=current_questions.values_list('question_id', flat=True))

    context = {
        'exam_paper': exam_paper,
        'current_questions': current_questions,
        'available_questions': available_questions
    }
    return render(request, 'teacher/exam_paper_questions.html', context)


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


@login_required
def exam_list(request):
    """考试列表视图"""
    exams = Exam.objects.filter(created_by=request.user).select_related('exam_paper', 'exam_paper__subject')

    # 为每个考试统计参加人数和完成人数
    for exam in exams:
        exam.participant_count = StudentExam.objects.filter(exam=exam).count()
        exam.completed_count = StudentExam.objects.filter(
            exam=exam,
            status='submitted'
        ).count()

        # 计算考试状态
        now = timezone.now()
        if exam.status == 'published':
            if now < exam.start_time:
                exam.status_display = '待开始'
            elif now > exam.end_time:
                exam.status_display = '已结束'
            else:
                exam.status_display = '进行中'
        else:
            exam.status_display = exam.get_status_display()

    context = {
        'exams': exams,
        'now': timezone.now()
    }
    return render(request, 'teacher/exam_list.html', context)


@login_required
def exam_grade(request, exam_id, student_id):
    """评分视图"""
    student_exam = get_object_or_404(
        StudentExam,
        exam_id=exam_id,  # 使用 exam_id 而不是 exam_paper_id
        student_id=student_id,
        exam__created_by=request.user,  # 通过 exam 关联检查创建者
        status='submitted'  # 只能评阅已提交的试卷
    )

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # 处理每道题的得分
                for answer in student_exam.student_answers.all():
                    score = request.POST.get(f'score_{answer.id}')
                    if score is not None:
                        try:
                            score = float(score)
                            if score < 0 or score > answer.question.score:
                                raise ValueError('分数超出范围')
                            answer.score = score
                            answer.save()
                        except ValueError:
                            messages.error(request, f'无效的分数格式：{score}')
                            return redirect('teacher:exam_grade', exam_id=exam_id, student_id=student_id)

                # 计算总分
                total_score = student_exam.student_answers.aggregate(
                    total=Sum('score')
                )['total'] or 0

                student_exam.total_score = total_score
                student_exam.status = 'graded'
                student_exam.save()

                messages.success(request, '评分完成！')
                return redirect('teacher:exam_detail', pk=exam_id)

        except Exception as e:
            messages.error(request, f'评分失败：{str(e)}')
            return redirect('teacher:exam_grade', exam_id=exam_id, student_id=student_id)

    # 获取所有答案及相关的试题信息
    answers = student_exam.student_answers.select_related('question').all()

    context = {
        'student_exam': student_exam,
        'answers': answers
    }
    return render(request, 'teacher/exam_grade.html', context)

@login_required
def exam_publish(request, pk):
    """发布考试视图"""
    exam_paper = get_object_or_404(ExamPaper, pk=pk, created_by=request.user)

    try:
        # 检查试卷是否满足发布条件
        if exam_paper.status != 'draft':
            messages.error(request, '只能发布草稿状态的试卷')
            return redirect('teacher:exam_detail', pk=pk)

        if exam_paper.question_count == 0:
            messages.error(request, '试卷必须包含至少一道试题')
            return redirect('teacher:exam_detail', pk=pk)

        if not exam_paper.start_time or not exam_paper.end_time:
            messages.error(request, '请设置考试开始和结束时间')
            return redirect('teacher:exam_detail', pk=pk)

        # 获取教师教授的班级学生
        teacher_classes = TeacherClass.objects.filter(
            teacher=request.user,
            subject=exam_paper.subject
        ).values_list('class_id', flat=True)

        students = UserProfile.objects.filter(
            role='student',
            class_id__in=teacher_classes
        ).select_related('user')

        # 为每个学生创建考试记录
        student_exams = []
        for profile in students:
            student_exams.append(StudentExam(
                student=profile.user,
                exam_paper=exam_paper
            ))

        with transaction.atomic():
            # 更新试卷状态
            exam_paper.status = 'published'
            exam_paper.save()

            # 批量创建学生考试记录
            StudentExam.objects.bulk_create(student_exams)

        messages.success(request, '考试发布成功')

    except Exception as e:
        messages.error(request, f'发布失败：{str(e)}')

    return redirect('teacher:exam_detail', pk=pk)


@login_required
def exam_close(request, pk):
    """关闭考试视图"""
    exam_paper = get_object_or_404(ExamPaper, pk=pk, created_by=request.user)

    try:
        if exam_paper.status != 'published':
            messages.error(request, '只能关闭已发布的考试')
            return redirect('teacher:exam_detail', pk=pk)

        with transaction.atomic():
            # 更新试卷状态
            exam_paper.status = 'ended'
            exam_paper.end_time = timezone.now()
            exam_paper.save()

            # 自动提交所有未交卷的考试记录
            unsubmitted_exams = StudentExam.objects.filter(
                exam_paper=exam_paper,
                status='in_progress'
            )

            for student_exam in unsubmitted_exams:
                student_exam.status = 'submitted'
                student_exam.submitted_at = timezone.now()

            StudentExam.objects.bulk_update(
                unsubmitted_exams,
                ['status', 'submitted_at']
            )

            # 对客观题进行自动评分
            student_answers = StudentAnswer.objects.filter(
                student_exam__exam_paper=exam_paper,
                score__isnull=True,
                question__type__in=['choice', 'true_false']
            )

            for answer in student_answers:
                answer.auto_grade()

        messages.success(request, '考试已关闭，客观题已自动评分')

    except Exception as e:
        messages.error(request, f'关闭失败：{str(e)}')

    return redirect('teacher:exam_detail', pk=pk)


@login_required
def exam_view_result(request, exam_id, student_id):
    """查看学生已评分的试卷"""
    student_exam = get_object_or_404(
        StudentExam,
        exam_paper_id=exam_id,
        student_id=student_id,
        exam_paper__created_by=request.user,
        status__in=['submitted', 'graded']  # 只能查看已提交或已评分的试卷
    )

    # 获取所有答案及相关的试题信息
    answers = (student_exam.student_answers.select_related('question')
               .order_by('question__type', 'question_id'))

    # 按题型分组
    answers_by_type = {}
    for answer in answers:
        question_type = answer.question.get_type_display()
        if question_type not in answers_by_type:
            answers_by_type[question_type] = []
        answers_by_type[question_type].append(answer)

    context = {
        'student_exam': student_exam,
        'answers_by_type': answers_by_type,
        'total_score': student_exam.total_score or 0,
        'can_edit': student_exam.status != 'graded'  # 已评分的试卷不能再编辑
    }
    return render(request, 'teacher/exam_view_result.html', context)
