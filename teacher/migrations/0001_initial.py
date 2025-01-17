# Generated by Django 5.1.4 on 2024-12-16 14:45

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='科目名称')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
            ],
            options={
                'verbose_name': '科目',
                'verbose_name_plural': '科目',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='ExamPaper',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='试卷名称')),
                ('total_score', models.PositiveIntegerField(verbose_name='总分')),
                ('question_count', models.PositiveIntegerField(default=0, verbose_name='题目数量')),
                ('duration', models.PositiveIntegerField(verbose_name='考试时长(分钟)')),
                ('start_time', models.DateTimeField(verbose_name='开始时间')),
                ('end_time', models.DateTimeField(verbose_name='结束时间')),
                ('status', models.CharField(choices=[('draft', '草稿'), ('published', '已发布'), ('ended', '已结束')], default='draft', max_length=20, verbose_name='状态')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_exam_papers', to=settings.AUTH_USER_MODEL, verbose_name='创建人')),
            ],
            options={
                'verbose_name': '试卷',
                'verbose_name_plural': '试卷',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('choice', '选择题'), ('true_false', '判断题'), ('subjective', '主观题')], max_length=20, verbose_name='题目类型')),
                ('content', models.TextField(verbose_name='题目内容')),
                ('options', models.JSONField(blank=True, help_text='选择题选项，JSON格式', null=True, verbose_name='选项')),
                ('correct_answer', models.TextField(verbose_name='正确答案')),
                ('score', models.PositiveIntegerField(verbose_name='分值')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_questions', to=settings.AUTH_USER_MODEL, verbose_name='创建人')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='teacher.subject', verbose_name='所属科目')),
            ],
            options={
                'verbose_name': '试题',
                'verbose_name_plural': '试题',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ExamQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.PositiveIntegerField(verbose_name='分值')),
                ('exam_paper', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='teacher.exampaper', verbose_name='试卷')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='teacher.question', verbose_name='试题')),
            ],
            options={
                'verbose_name': '试卷试题',
                'verbose_name_plural': '试卷试题',
                'unique_together': {('exam_paper', 'question')},
            },
        ),
        migrations.AddField(
            model_name='exampaper',
            name='questions',
            field=models.ManyToManyField(related_name='exam_papers', through='teacher.ExamQuestion', to='teacher.question', verbose_name='试题'),
        ),
        migrations.AddField(
            model_name='exampaper',
            name='subject',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='exam_papers', to='teacher.subject', verbose_name='所属科目'),
        ),
    ]
