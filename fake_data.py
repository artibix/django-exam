# generate_fake_data.py

import os
import sys
import django
import random
from datetime import timedelta
from faker import Faker

# Set up Django environment
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Exam.settings')
django.setup()

# Now import Django models after environment setup
from django.utils import timezone
from django.contrib.auth.models import User
from users.models import UserProfile, Class
from teacher.models import (
    Subject, Question, ExamPaper, Exam, ExamQuestion,
    TeacherClass, StudentExam, StudentAnswer, Announcement,
    GradeAnalysis
)

fake = Faker(['zh_CN'])


def create_classes(num_classes=10):
    """创建班级数据"""
    classes = []
    for i in range(num_classes):
        class_obj = Class.objects.create(
            name=f"{random.randint(2020, 2023)}级{random.randint(1, 4)}班"
        )
        classes.append(class_obj)
    return classes


def create_users_and_profiles(num_students=50, num_teachers=10):
    """创建用户和用户档案数据"""
    users = []
    classes = Class.objects.all()

    # 创建一个管理员
    admin = User.objects.create_user(
        username='admin',
        password='admin123',
        email=fake.email(),
        first_name=fake.first_name(),
        last_name=fake.last_name(),
    )
    UserProfile.objects.create(
        user=admin,
        phone=fake.phone_number(),
        gender=random.choice(['M', 'F']),
        role='admin'
    )

    # 创建教师
    for i in range(num_teachers):
        teacher = User.objects.create_user(
            username=f'teacher{i + 1}',
            password='password123',
            email=fake.email(),
            first_name=fake.first_name(),
            last_name=fake.last_name(),
        )
        UserProfile.objects.create(
            user=teacher,
            phone=fake.phone_number(),
            gender=random.choice(['M', 'F']),
            role='teacher'
        )
        users.append(teacher)

    # 创建学生
    for i in range(num_students):
        student = User.objects.create_user(
            username=f'student{i + 1}',
            password='password123',
            email=fake.email(),
            first_name=fake.first_name(),
            last_name=fake.last_name(),
        )
        UserProfile.objects.create(
            user=student,
            phone=fake.phone_number(),
            gender=random.choice(['M', 'F']),
            role='student',
            class_id=random.choice(classes)
        )
        users.append(student)

    return users


def create_subjects():
    """创建科目数据"""
    subjects = ['语文', '数学', '英语', '物理', '化学', '生物', '历史', '地理', '政治']
    created_subjects = []
    for subject_name in subjects:
        subject = Subject.objects.create(name=subject_name)
        created_subjects.append(subject)
    return created_subjects


def create_questions(subjects, teachers, num_questions=200):
    """创建试题数据"""
    questions = []
    for _ in range(num_questions):
        question_type = random.choice(['single_choice', 'true_false', 'subjective'])

        if question_type == 'single_choice':
            options = {
                'A': fake.sentence(),
                'B': fake.sentence(),
                'C': fake.sentence(),
                'D': fake.sentence()
            }
            correct_answer = random.choice(['A', 'B', 'C', 'D'])
        elif question_type == 'true_false':
            options = None
            correct_answer = random.choice(['T', 'F'])
        else:
            options = None
            correct_answer = fake.paragraph()

        question = Question.objects.create(
            subject=random.choice(subjects),
            type=question_type,
            content=fake.paragraph(),
            options=options,
            correct_answer=correct_answer,
            score=random.choice([2, 3, 5, 10]),
            created_by=random.choice(teachers)
        )
        questions.append(question)
    return questions


def create_exam_papers(subjects, teachers, questions, num_papers=20):
    """创建试卷数据"""
    exam_papers = []
    for _ in range(num_papers):
        subject = random.choice(subjects)
        subject_questions = [q for q in questions if q.subject == subject]

        if len(subject_questions) < 10:
            continue

        selected_questions = random.sample(subject_questions, 10)
        total_score = sum(q.score for q in selected_questions)

        exam_paper = ExamPaper.objects.create(
            name=f"{subject.name}试卷{fake.random_int(min=1, max=100)}",
            subject=subject,
            total_score=total_score,
            question_count=len(selected_questions),
            created_by=random.choice(teachers)
        )

        # 创建试卷试题关联
        for question in selected_questions:
            ExamQuestion.objects.create(
                exam_paper=exam_paper,
                question=question,
                score=question.score
            )

        exam_papers.append(exam_paper)
    return exam_papers


def create_exams(exam_papers, teachers, classes, num_exams=15):
    """创建考试数据"""
    exams = []
    now = timezone.now()

    for _ in range(num_exams):
        start_time = now + timedelta(days=random.randint(-30, 30))
        duration = random.randint(60, 180)

        exam = Exam.objects.create(
            name=f"{random.choice(exam_papers).name}考试",
            exam_paper=random.choice(exam_papers),
            duration=duration,
            start_time=start_time,
            end_time=start_time + timedelta(minutes=duration),
            created_by=random.choice(teachers),
            description=fake.paragraph()
        )

        # 随机分配参与班级
        selected_classes = random.sample(classes, random.randint(1, 3))
        exam.classes.set(selected_classes)
        exam.update_status()
        exams.append(exam)

    return exams


def create_teacher_classes(teachers, classes, subjects):
    """创建教师班级关联数据"""
    for teacher in teachers:
        # 为每个教师随机分配2-3个班级和科目
        num_classes = random.randint(2, 3)
        for _ in range(num_classes):
            TeacherClass.objects.create(
                teacher=teacher,
                class_id=random.choice(classes),
                subject=random.choice(subjects)
            )


def create_student_exams(students, exams):
    """创建学生考试记录数据"""
    for exam in exams:
        # 获取参与考试的班级的学生
        eligible_students = [s for s in students
                             if hasattr(s.userprofile, 'class_id') and
                             s.userprofile.class_id in exam.classes.all()]

        for student in eligible_students:
            # 随机决定是否已完成考试
            if random.random() < 0.8:  # 80%的概率完成考试
                student_exam = StudentExam.objects.create(
                    student=student,
                    exam=exam,
                    submitted_at=exam.start_time + timedelta(minutes=random.randint(30, exam.duration)),
                    status='submitted'
                )

                # 创建学生答案
                exam_questions = ExamQuestion.objects.filter(exam_paper=exam.exam_paper)
                for exam_question in exam_questions:
                    question = exam_question.question
                    if question.type == 'single_choice':
                        answer = random.choice(['A', 'B', 'C', 'D'])
                    elif question.type == 'true_false':
                        answer = random.choice(['T', 'F'])
                    else:
                        answer = fake.paragraph()

                    student_answer = StudentAnswer.objects.create(
                        student_exam=student_exam,
                        question=question,
                        answer_text=answer
                    )

                    # 自动评分客观题
                    if question.is_objective():
                        student_answer.auto_grade()
                    else:
                        # 主观题随机打分
                        student_answer.score = random.uniform(0, question.score)
                        student_answer.save()

                # 计算总分
                student_exam.grade()


def create_announcements(teachers, classes, students, num_announcements=30):
    """创建通知公告数据"""
    for _ in range(num_announcements):
        announcement_type = random.choice(['all', 'class', 'personal'])
        teacher = random.choice(teachers)

        if announcement_type == 'class':
            receiver_class = random.choice(classes)
            Announcement.objects.create(
                title=fake.sentence(),
                content=fake.paragraph(),
                sender=teacher,
                receiver_class=receiver_class,
                type='class'
            )
        elif announcement_type == 'personal':
            receiver = random.choice(students)
            Announcement.objects.create(
                title=fake.sentence(),
                content=fake.paragraph(),
                sender=teacher,
                receiver=receiver,
                type='personal'
            )
        else:
            Announcement.objects.create(
                title=fake.sentence(),
                content=fake.paragraph(),
                sender=teacher,
                type='all'
            )


def create_grade_analyses(exams):
    """创建成绩分析数据"""
    for exam in exams:
        for class_obj in exam.classes.all():
            student_exams = StudentExam.objects.filter(
                exam=exam,
                student__userprofile__class_id=class_obj,
                status='graded'
            )

            if not student_exams.exists():
                continue

            scores = [se.total_score for se in student_exams if se.total_score is not None]
            if not scores:
                continue

            # 计算分数分布
            score_ranges = {
                '0-60': 0,
                '60-70': 0,
                '70-80': 0,
                '80-90': 0,
                '90-100': 0
            }

            for score in scores:
                if score < 60:
                    score_ranges['0-60'] += 1
                elif score < 70:
                    score_ranges['60-70'] += 1
                elif score < 80:
                    score_ranges['70-80'] += 1
                elif score < 90:
                    score_ranges['80-90'] += 1
                else:
                    score_ranges['90-100'] += 1

            GradeAnalysis.objects.create(
                exam=exam,
                class_id=class_obj,
                total_students=len(scores),
                average_score=sum(scores) / len(scores),
                highest_score=max(scores),
                lowest_score=min(scores),
                passing_rate=len([s for s in scores if s >= 60]) / len(scores) * 100,
                score_distribution=score_ranges
            )


def main():
    """主函数"""
    print("开始生成测试数据...")

    # 创建基础数据
    classes = create_classes(10)
    print("✓ 已创建班级数据")

    users = create_users_and_profiles(50, 10)
    print("✓ 已创建用户数据")

    subjects = create_subjects()
    print("✓ 已创建科目数据")

    # 获取教师和学生用户
    teachers = User.objects.filter(userprofile__role='teacher')
    students = User.objects.filter(userprofile__role='student')

    # 创建教学相关数据
    questions = create_questions(subjects, teachers, 200)
    print("✓ 已创建试题数据")

    exam_papers = create_exam_papers(subjects, teachers, questions, 20)
    print("✓ 已创建试卷数据")

    exams = create_exams(exam_papers, teachers, classes, 15)
    print("✓ 已创建考试数据")

    create_teacher_classes(teachers, classes, subjects)
    print("✓ 已创建教师班级关联")

    create_student_exams(students, exams)
    print("✓ 已创建学生考试记录")

    create_announcements(teachers, classes, students, 30)
    print("✓ 已创建通知公告")

    create_grade_analyses(exams)
    print("✓ 已创建成绩分析")

    print("\n测试数据生成完成!")


if __name__ == '__main__':
    main()
