# exam/models.py

from django.db import models
from django.contrib.auth.models import User

from users.models import Class


class Subject(models.Model):
    """科目模型"""
    name = models.CharField(max_length=255, unique=True, verbose_name='科目名称')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '科目'
        verbose_name_plural = '科目'
        ordering = ['name']

    def __str__(self):
        return self.name


class Question(models.Model):
    """试题模型"""
    QUESTION_TYPES = (
        ('choice', '选择题'),
        ('true_false', '判断题'),
        ('subjective', '主观题'),
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name='所属科目'
    )
    type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPES,
        verbose_name='题目类型'
    )
    content = models.TextField(verbose_name='题目内容')
    options = models.JSONField(
        null=True,
        blank=True,
        verbose_name='选项',
        help_text='选择题选项，JSON格式'
    )
    correct_answer = models.TextField(verbose_name='正确答案')
    score = models.PositiveIntegerField(verbose_name='分值')
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_questions',
        verbose_name='创建人'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '试题'
        verbose_name_plural = '试题'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_type_display()}: {self.content[:50]}'


class ExamPaper(models.Model):
    """试卷模型"""
    STATUS_CHOICES = (
        ('draft', '草稿'),
        ('published', '已发布'),
        ('ended', '已结束'),
    )

    name = models.CharField(max_length=255, verbose_name='试卷名称')
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='exam_papers',
        verbose_name='所属科目'
    )
    total_score = models.PositiveIntegerField(verbose_name='总分')
    question_count = models.PositiveIntegerField(
        default=0,
        verbose_name='题目数量'
    )
    duration = models.PositiveIntegerField(verbose_name='考试时长(分钟)')
    start_time = models.DateTimeField(verbose_name='开始时间')
    end_time = models.DateTimeField(verbose_name='结束时间')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='状态'
    )
    questions = models.ManyToManyField(
        Question,
        through='ExamQuestion',
        related_name='exam_papers',
        verbose_name='试题'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_exam_papers',
        verbose_name='创建人'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '试卷'
        verbose_name_plural = '试卷'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class ExamQuestion(models.Model):
    """试卷试题关联模型"""
    exam_paper = models.ForeignKey(
        ExamPaper,
        on_delete=models.CASCADE,
        verbose_name='试卷'
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        verbose_name='试题'
    )
    score = models.PositiveIntegerField(verbose_name='分值')

    class Meta:
        verbose_name = '试卷试题'
        verbose_name_plural = '试卷试题'
        unique_together = ['exam_paper', 'question']

    def __str__(self):
        return f'{self.exam_paper.name} - {self.question.content[:30]}'


class TeacherClass(models.Model):
    """教师班级关联模型"""
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='teaching_classes',
        verbose_name='教师'
    )
    class_id = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='teacher_classes',
        verbose_name='班级'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='teacher_classes',
        verbose_name='科目'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '教师班级关联'
        verbose_name_plural = '教师班级关联'
        unique_together = ['teacher', 'class_id', 'subject']

    def __str__(self):
        return f'{self.teacher.get_full_name()} - {self.class_id.name} - {self.subject.name}'


from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class StudentExam(models.Model):
    """学生考试记录模型"""
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='student_exams',
        verbose_name='学生'
    )
    exam_paper = models.ForeignKey(
        'ExamPaper',
        on_delete=models.CASCADE,
        related_name='student_exams',
        verbose_name='试卷'
    )
    total_score = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name='总分'
    )
    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='开始时间'
    )
    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='提交时间'
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('in_progress', '进行中'),
            ('submitted', '已提交'),
            ('graded', '已批改'),
        ],
        default='in_progress',
        verbose_name='状态'
    )

    class Meta:
        verbose_name = '学生考试记录'
        verbose_name_plural = '学生考试记录'
        unique_together = ['student', 'exam_paper']
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.student.username} - {self.exam_paper.name}"

    def submit(self):
        """提交试卷"""
        if self.status == 'in_progress':
            self.submitted_at = timezone.now()
            self.status = 'submitted'
            self.save()

    def grade(self):
        """计算总分"""
        total = self.student_answers.aggregate(
            total=models.Sum('score')
        )['total'] or 0
        self.total_score = total
        self.status = 'graded'
        self.save()


class StudentAnswer(models.Model):
    """学生答案模型"""
    student_exam = models.ForeignKey(
        StudentExam,
        on_delete=models.CASCADE,
        related_name='student_answers',
        verbose_name='考试记录'
    )
    question = models.ForeignKey(
        'Question',
        on_delete=models.CASCADE,
        related_name='student_answers',
        verbose_name='试题'
    )
    answer_text = models.TextField(
        verbose_name='答案内容'
    )
    score = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name='得分'
    )
    auto_graded = models.BooleanField(
        default=False,
        verbose_name='是否自动评分'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='更新时间'
    )

    class Meta:
        verbose_name = '学生答案'
        verbose_name_plural = '学生答案'
        unique_together = ['student_exam', 'question']
        ordering = ['question_id']

    def __str__(self):
        return f"{self.student_exam.student.username} - {self.question.content[:20]}"

    def auto_grade(self):
        """自动评分（用于客观题）"""
        if self.question.type in ['choice', 'true_false']:
            if self.answer_text.strip() == self.question.correct_answer.strip():
                self.score = self.question.score
            else:
                self.score = 0
            self.auto_graded = True
            self.save()
