# users/models.py

from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('student', '学生'),
        ('teacher', '教师'),
        ('admin', '管理员'),
    )
    GENDER_CHOICES = (
        ('M', '男'),
        ('F', '女'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=11, blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    class_id = models.ForeignKey('Class', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"


class Class(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
