# Generated by Django 5.1.4 on 2024-12-20 16:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('teacher', '0003_studentexam_studentanswer'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentanswer',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='teacher.question',
                                    verbose_name='试题'),
        ),
    ]
