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
    options_text = forms.CharField(
        label='选项',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': '每行输入一个选项，例如：\nA. 选项1\nB. 选项2'
        }),
        help_text='选择题必填，每行输入一个选项'
    )

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
            'correct_answer': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': '请输入正确答案'
            }),
            'score': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入分值'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 如果是编辑模式，显示已有的选项
        instance = kwargs.get('instance')
        if instance and instance.type == 'choice' and instance.options:
            options = instance.options.get('options', [])
            self.fields['options_text'].initial = '\n'.join(options)

    def clean(self):
        cleaned_data = super().clean()
        question_type = cleaned_data.get('type')
        options_text = cleaned_data.get('options_text', '')

        if question_type == 'choice':
            # 处理选择题选项
            if not options_text.strip():
                raise forms.ValidationError('选择题必须包含选项')

            # 将选项文本分割成列表，去除空行
            options_list = [opt.strip() for opt in options_text.split('\n') if opt.strip()]

            if len(options_list) < 2:
                raise forms.ValidationError('选择题至少需要两个选项')

            # 保存选项到cleaned_data
            cleaned_data['options'] = {'options': options_list}
        else:
            cleaned_data['options'] = None

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # 保存选项
        if self.cleaned_data.get('type') == 'choice':
            instance.options = self.cleaned_data.get('options')
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
