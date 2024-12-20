# teacher/forms.py

from django import forms
from django.core.exceptions import ValidationError

from teacher.models import ExamPaper, Question, Subject, TeacherClass


class TeacherLoginForm(forms.Form):
    username = forms.CharField(
        label='用户名',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '请输入用户名'
        })
    )
    password = forms.CharField(
        label='密码',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '请输入密码'
        })
    )


class ExamPaperForm(forms.ModelForm):
    """试卷基本信息表单"""

    class Meta:
        model = ExamPaper
        fields = ['name', 'subject', 'total_score', 'duration', 'start_time', 'end_time']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入试卷名称'
            }),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'total_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入总分'
            }),
            'duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入考试时长（分钟）'
            }),
            'start_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'end_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            })
        }
        labels = {
            'name': '试卷名称',
            'subject': '科目',
            'total_score': '总分',
            'duration': '考试时长',
            'start_time': '开始时间',
            'end_time': '结束时间'
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time and start_time >= end_time:
            raise ValidationError('结束时间必须晚于开始时间')

        return cleaned_data


class QuestionSelectionForm(forms.Form):
    """试题选择表单"""
    questions = forms.ModelMultipleChoiceField(
        queryset=Question.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label='选择试题'
    )

    def __init__(self, subject, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['questions'].queryset = Question.objects.filter(subject=subject)


class QuestionForm(forms.ModelForm):
    """试题表单"""
    option_a = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    option_b = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    option_c = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    option_d = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Question
        fields = ['subject', 'type', 'content', 'correct_answer', 'score']
        widgets = {
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '请输入题目内容'
            }),
            'correct_answer': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '单选题填写A/B/C/D，判断题填写T/F'
            }),
            'score': forms.NumberInput(attrs={
                'class': 'form-control',
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance and instance.type == 'single_choice' and instance.options:
            for key, value in instance.options.items():
                field_name = f'option_{key.lower()}'
                if hasattr(self, field_name):
                    self.fields[field_name].initial = value

    def clean(self):
        cleaned_data = super().clean()
        question_type = cleaned_data.get('type')
        correct_answer = cleaned_data.get('correct_answer', '').strip().upper()

        if question_type == 'single_choice':
            # 验证选项
            options = {}
            for key in ['A', 'B', 'C', 'D']:
                value = cleaned_data.get(f'option_{key.lower()}', '').strip()
                if not value:
                    raise forms.ValidationError(f'选项{key}不能为空')
                options[key] = value

            # 验证答案
            if correct_answer not in ['A', 'B', 'C', 'D']:
                raise forms.ValidationError('单选题答案必须是A、B、C、D之一')

            cleaned_data['options'] = options

        elif question_type == 'true_false':
            if correct_answer not in ['T', 'F']:
                raise forms.ValidationError('判断题答案必须是T或F')
            cleaned_data['options'] = None
        else:
            cleaned_data['options'] = None

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.type == 'single_choice':
            instance.options = self.cleaned_data['options']
        else:
            instance.options = None
        if commit:
            instance.save()
        return instance

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'})
        }


class TeacherClassForm(forms.ModelForm):
    class Meta:
        model = TeacherClass
        fields = ['class_id', 'subject']
        widgets = {
            'class_id': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-control'})
        }
