# student/views.py
from django.db.models import Avg
from django.urls import reverse

from teacher.models import StudentExam, StudentAnswer, Question, Exam

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db import transaction


@login_required
def dashboard(request):
    """学生仪表板"""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'student':
        messages.error(request, '您没有权限访问学生系统')
        return redirect('login')

    # 获取当前进行中的考试
    current_exams = StudentExam.objects.filter(
        student=request.user,
        exam__status='in_progress',
        status='in_progress'
    ).select_related('exam', 'exam__exam_paper', 'exam__exam_paper__subject')

    # 获取即将开始的考试
    upcoming_exams = StudentExam.objects.filter(
        student=request.user,
        exam__status='preparing',
        status='in_progress'
    ).select_related('exam', 'exam__exam_paper', 'exam__exam_paper__subject')

    # 获取已完成的考试
    completed_exams = StudentExam.objects.filter(
        student=request.user,
        status__in=['submitted', 'graded']
    ).select_related('exam', 'exam__exam_paper', 'exam__exam_paper__subject')

    context = {
        'current_exams': current_exams,
        'upcoming_exams': upcoming_exams,
        'completed_exams': completed_exams,
    }
    return render(request, 'student/dashboard.html', context)


@login_required
def exam_detail(request, pk):
    """考试详情和答题界面"""
    # 修改查询条件，确保获取正确的考试记录
    student_exam = get_object_or_404(
        StudentExam,
        student=request.user,
        exam_id=pk
    )
    exam = student_exam.exam

    # 检查考试时间和状态
    now = timezone.now()
    if now < exam.start_time:
        messages.error(request, '考试还未开始')
        return redirect('student:dashboard')

    if now > exam.end_time or student_exam.status != 'in_progress':
        messages.error(request, '考试已结束')
        return redirect('student:dashboard')

    # 计算剩余时间
    end_time = min(exam.end_time, exam.start_time + timezone.timedelta(minutes=exam.duration))
    remaining_seconds = int((end_time - now).total_seconds())
    remaining_seconds = max(remaining_seconds, 0)

    # 获取试题和答案
    exam_questions = exam.exam_paper.examquestion_set.select_related('question').all()
    student_answers = StudentAnswer.objects.filter(student_exam=student_exam)
    answers_dict = {answer.question_id: answer.answer_text for answer in student_answers}

    context = {
        'student_exam': student_exam,
        'exam_questions': exam_questions,
        'student_answers': answers_dict,
        'remaining_seconds': remaining_seconds
    }
    return render(request, 'student/exam_detail.html', context)


@login_required
def exam_start(request, pk):
    """开始考试"""
    student_exam = get_object_or_404(
        StudentExam,
        pk=pk,
        student=request.user,
        exam__status='in_progress',
        status='in_progress'
    )

    # 检查考试时间
    now = timezone.now()
    if now < student_exam.exam.start_time:
        messages.error(request, '考试还未开始')
        return redirect('student:dashboard')

    if now > student_exam.exam.end_time:
        messages.error(request, '考试已结束')
        return redirect('student:dashboard')

    # 初始化答题记录
    questions = student_exam.exam.exam_paper.examquestion_set.all()
    with transaction.atomic():
        for exam_question in questions:
            StudentAnswer.objects.get_or_create(
                student_exam=student_exam,
                question=exam_question.question,
                defaults={'answer_text': ''}
            )

    return redirect('student:exam_detail', pk=pk)


@login_required
def exam_auto_submit(request, pk):
    """考试时间结束自动提交"""
    student_exam = get_object_or_404(
        StudentExam,
        pk=pk,
        student=request.user,
        status='in_progress'
    )

    if timezone.now() >= student_exam.exam.end_time:
        with transaction.atomic():
            student_exam.status = 'submitted'
            student_exam.submitted_at = timezone.now()
            student_exam.save()

            # 对客观题进行自动评分
            auto_grade_answers(student_exam)

        return JsonResponse({
            'status': 'success',
            'message': '考试已自动提交',
            'redirect_url': reverse('student:dashboard')
        })

    return JsonResponse({'status': 'error', 'message': '考试尚未结束'})


@login_required
def exam_submit(request, pk):
    """保存或提交答案"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': '无效的请求方法'})

    student_exam = get_object_or_404(
        StudentExam,
        pk=pk,
        student=request.user,
        status='in_progress'
    )

    try:
        # 获取答案数据
        question_id = request.POST.get('question_id')
        answer_text = request.POST.get('answer')
        is_final_submit = request.POST.get('is_final_submit') == 'true'

        with transaction.atomic():
            # 更新或创建答案
            if question_id:
                question = get_object_or_404(Question, id=question_id)
                # 处理选择题答案
                if question.type == 'single_choice':
                    # 将数字选项转换为字母选项
                    if answer_text.isdigit():
                        # 1->A, 2->B, 3->C, 4->D
                        answer_text = chr(64 + int(answer_text))

                # 处理判断题答案
                elif question.type == 'true_false':
                    answer_text = 'T' if answer_text.lower() == 'true' else 'F'

                answer, _ = StudentAnswer.objects.get_or_create(
                    student_exam=student_exam,
                    question_id=question_id,
                    defaults={'answer_text': answer_text}
                )
                if answer.answer_text != answer_text:
                    answer.answer_text = answer_text
                    answer.save()

            # 如果是最终提交
            if is_final_submit:
                student_exam.status = 'submitted'
                student_exam.submitted_at = timezone.now()
                student_exam.save()

                # 对客观题进行自动评分
                auto_grade_answers(student_exam)

                return JsonResponse({
                    'status': 'success',
                    'message': '考试提交成功',
                    'redirect_url': reverse('student:dashboard')
                })

        return JsonResponse({'status': 'success', 'message': '答案保存成功'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


def auto_grade_answers(student_exam):
    """自动评分工具函数"""
    answers = StudentAnswer.objects.filter(
        student_exam=student_exam,
        question__type__in=['single_choice', 'true_false']
    ).select_related('question')

    for answer in answers:
        if answer.question.check_answer(answer.answer_text):
            answer.score = answer.question.score
        else:
            answer.score = 0
        answer.auto_graded = True
        answer.save()
