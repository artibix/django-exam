# Generated by Django 5.1.4 on 2024-12-16 14:57

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('teacher', '0001_initial'),
        ('users', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TeacherClass',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('class_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='teacher_classes', to='users.class', verbose_name='班级')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='teacher_classes', to='teacher.subject', verbose_name='科目')),
                ('teacher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='teaching_classes', to=settings.AUTH_USER_MODEL, verbose_name='教师')),
            ],
            options={
                'verbose_name': '教师班级关联',
                'verbose_name_plural': '教师班级关联',
                'unique_together': {('teacher', 'class_id', 'subject')},
            },
        ),
    ]
