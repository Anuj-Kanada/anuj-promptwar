from django.contrib import admin
from .models import StudentProfile


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'exam_type', 'exam_date', 'daily_study_hours', 'created_at']
    list_filter = ['exam_type']
    search_fields = ['user__username', 'user__email']
