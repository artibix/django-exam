# admin_site/forms.py

from django import forms
from django.contrib.auth.models import User
from users.models import UserProfile, Class


class TeacherForm(forms.Form):
    """教师信息表单"""
    username = forms.CharField(
        label='用户名',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label='邮箱',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label='密码',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text='创建时必填，修改时可选'
    )
    first_name = forms.CharField(
        label='名',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        label='姓',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        label='手机号',
        max_length=11,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    gender = forms.ChoiceField(
        label='性别',
        choices=UserProfile.GENDER_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


# admin_site/forms.py

class StudentForm(forms.Form):
    """Student information form"""
    username = forms.CharField(
        label='用户名',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label='邮箱',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label='密码',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text='创建时必填，修改时可选'
    )
    first_name = forms.CharField(
        label='名',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        label='姓',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        label='手机号',
        max_length=11,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    gender = forms.ChoiceField(
        label='性别',
        choices=UserProfile.GENDER_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    class_id = forms.ModelChoiceField(
        label='班级',
        queryset=Class.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )


class ClassForm(forms.ModelForm):
    """班级信息表单"""

    class Meta:
        model = Class
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'})
        }
        labels = {
            'name': '班级名称'
        }


class TeacherSearchForm(forms.Form):
    """教师查询表单"""
    search_term = forms.CharField(
        label='搜索',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '输入姓名、用户名或邮箱搜索'
        })
    )


class StudentSearchForm(forms.Form):
    """学生查询表单"""
    search_term = forms.CharField(
        label='搜索',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '输入姓名、用户名或邮箱搜索'
        })
    )
    class_id = forms.ModelChoiceField(
        label='班级',
        queryset=Class.objects.all(),
        required=False,
        empty_label="所有班级",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
