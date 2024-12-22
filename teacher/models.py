# teacher/models.py

from django.contrib.auth.models import User

from users.models import Class

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


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
        ('single_choice', '单选题'),
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
        help_text='单选题选项，格式：{"A": "选项内容", "B": "选项内容", ...}'
    )
    correct_answer = models.CharField(
        max_length=255,
        verbose_name='正确答案',
        help_text='单选题填写选项字母(A/B/C/D)，判断题填写(T/F)'
    )
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

    def get_formatted_options(self):
        """获取格式化的选项"""
        if self.type == 'single_choice' and self.options:
            return [f"{k}. {v}" for k, v in self.options.items()]
        return []

    def is_objective(self):
        """是否为客观题"""
        return self.type in ['single_choice', 'true_false']

    def check_answer(self, student_answer):
        """检查答案是否正确"""
        if not self.is_objective():
            return None

        if self.type == 'single_choice':
            return student_answer.strip().upper() == self.correct_answer.strip().upper()
        elif self.type == 'true_false':
            return student_answer.strip().upper() == self.correct_answer.strip().upper()


class ExamPaper(models.Model):
    """试卷模型"""
    name = models.CharField(max_length=255, verbose_name='试卷名称')
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='exam',
        verbose_name='所属科目'
    )
    total_score = models.PositiveIntegerField(verbose_name='总分')
    question_count = models.PositiveIntegerField(
        default=0,
        verbose_name='题目数量'
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


class Exam(models.Model):
    """考试模型"""
    STATUS_CHOICES = (
        ('preparing', '准备中'),
        ('in_progress', '进行中'),
        ('ended', '已结束'),
    )

    name = models.CharField(max_length=255, verbose_name='考试名称')
    exam_paper = models.ForeignKey(
        ExamPaper,
        on_delete=models.PROTECT,  # 防止删除正在使用的试卷
        related_name='exams',
        verbose_name='试卷'
    )
    classes = models.ManyToManyField(
        Class,
        related_name='exams',
        verbose_name='参与班级'
    )
    duration = models.PositiveIntegerField(verbose_name='考试时长(分钟)')
    start_time = models.DateTimeField(verbose_name='开始时间')
    end_time = models.DateTimeField(verbose_name='结束时间')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='preparing',
        verbose_name='状态'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_exams',
        verbose_name='创建人'
    )
    description = models.TextField(
        blank=True,
        verbose_name='考试说明'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '考试'
        verbose_name_plural = '考试'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def update_status(self):
        """更新考试状态"""
        now = timezone.now()
        if now < self.start_time:
            new_status = 'preparing'
        elif self.start_time <= now <= self.end_time:
            new_status = 'in_progress'
        else:
            new_status = 'ended'

        if new_status != self.status:
            self.status = new_status
            self.save()


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


class StudentExam(models.Model):
    """学生考试记录模型"""
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='student_exams',
        verbose_name='学生'
    )

    exam = models.ForeignKey(  # 改为关联 Exam
        'Exam',
        on_delete=models.CASCADE,
        related_name='student_exams',
        verbose_name='考试',
        null=True
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
        unique_together = ['student', 'exam']
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.student.username} - {self.exam.name}"

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
        related_name='student_answers',  # 添加 related_name
        verbose_name='考试记录'
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        verbose_name='试题'
    )
    answer_text = models.TextField(verbose_name='答案内容')
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
        """自动评分"""
        if not self.question.is_objective():
            return False

        student_answer = self.answer_text.strip()
        if self.question.check_answer(student_answer):
            self.score = self.question.score
        else:
            self.score = 0

        self.auto_graded = True
        self.save()
        return True


# teacher/models.py 中添加

class Announcement(models.Model):
    """通知公告模型"""
    ANNOUNCEMENT_TYPES = (
        ('all', '全体通知'),
        ('class', '班级通知'),
        ('personal', '个人通知')
    )

    title = models.CharField(max_length=255, verbose_name='标题')
    content = models.TextField(verbose_name='内容')
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_announcements',
        verbose_name='发送者'
    )
    receiver_class = models.ForeignKey(
        'users.Class',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='received_announcements',
        verbose_name='接收班级'
    )
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='received_announcements',
        verbose_name='接收者'
    )
    type = models.CharField(
        max_length=20,
        choices=ANNOUNCEMENT_TYPES,
        default='all',
        verbose_name='通知类型'
    )
    is_read = models.BooleanField(default=False, verbose_name='是否已读')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '通知公告'
        verbose_name_plural = '通知公告'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    # teacher/models.py


class GradeAnalysis(models.Model):
    """成绩分析模型"""
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name='grade_analyses',
        verbose_name='考试'
    )
    class_id = models.ForeignKey(
        'users.Class',
        on_delete=models.CASCADE,
        verbose_name='班级'
    )
    total_students = models.IntegerField(verbose_name='总人数')
    average_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='平均分'
    )
    highest_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='最高分'
    )
    lowest_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='最低分'
    )
    passing_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='及格率'
    )
    score_distribution = models.JSONField(
        verbose_name='分数分布',
        help_text='格式：{"0-60": 10, "60-70": 20, ...}'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间'
    )

    class Meta:
        verbose_name = '成绩分析'
        verbose_name_plural = '成绩分析'
        ordering = ['-created_at']
