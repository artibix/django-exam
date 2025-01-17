# Generated by Django 5.1.4 on 2024-12-21 03:03

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('teacher', '0005_alter_question_correct_answer_alter_question_options_and_more'),
        ('users', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='exampaper',
            name='duration',
        ),
        migrations.RemoveField(
            model_name='exampaper',
            name='end_time',
        ),
        migrations.RemoveField(
            model_name='exampaper',
            name='questions',
        ),
        migrations.RemoveField(
            model_name='exampaper',
            name='start_time',
        ),
        migrations.RemoveField(
            model_name='exampaper',
            name='status',
        ),
        migrations.AddField(
            model_name='exampaper',
            name='is_template',
            field=models.BooleanField(default=False, verbose_name='是否为模板'),
        ),
        migrations.CreateModel(
            name='Exam',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='考试名称')),
                ('duration', models.PositiveIntegerField(verbose_name='考试时长(分钟)')),
                ('start_time', models.DateTimeField(verbose_name='开始时间')),
                ('end_time', models.DateTimeField(verbose_name='结束时间')),
                ('status', models.CharField(choices=[('preparing', '准备中'), ('in_progress', '进行中'), ('ended', '已结束')], default='preparing', max_length=20, verbose_name='状态')),
                ('description', models.TextField(blank=True, verbose_name='考试说明')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('classes', models.ManyToManyField(related_name='exams', to='users.class', verbose_name='参与班级')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_exams', to=settings.AUTH_USER_MODEL, verbose_name='创建人')),
                ('exam_paper', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='exams', to='teacher.exampaper', verbose_name='试卷')),
            ],
            options={
                'verbose_name': '考试',
                'verbose_name_plural': '考试',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='studentexam',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='studentexam',
            name='exam',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='student_exams', to='teacher.exam', verbose_name='考试'),
        ),
        migrations.AlterUniqueTogether(
            name='studentexam',
            unique_together={('student', 'exam')},
        ),
        migrations.RemoveField(
            model_name='studentexam',
            name='exam_paper',
        ),
    ]
