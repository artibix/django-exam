# Generated by Django 5.1.4 on 2024-12-20 17:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('teacher', '0004_alter_studentanswer_question'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='correct_answer',
            field=models.CharField(help_text='单选题填写选项字母(A/B/C/D)，判断题填写(T/F)', max_length=255, verbose_name='正确答案'),
        ),
        migrations.AlterField(
            model_name='question',
            name='options',
            field=models.JSONField(blank=True, help_text='单选题选项，格式：{"A": "选项内容", "B": "选项内容", ...}', null=True, verbose_name='选项'),
        ),
        migrations.AlterField(
            model_name='question',
            name='type',
            field=models.CharField(choices=[('single_choice', '单选题'), ('true_false', '判断题'), ('subjective', '主观题')], max_length=20, verbose_name='题目类型'),
        ),
    ]
