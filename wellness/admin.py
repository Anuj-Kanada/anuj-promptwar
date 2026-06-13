from django.contrib import admin
from .models import WellnessAlert, MindfulnessExercise

@admin.register(WellnessAlert)
class WellnessAlertAdmin(admin.ModelAdmin):
    list_display = ['user', 'alert_type', 'severity', 'title', 'is_read', 'created_at']
    list_filter = ['alert_type', 'severity', 'is_read']

@admin.register(MindfulnessExercise)
class MindfulnessExerciseAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'duration_minutes', 'difficulty']
    list_filter = ['category', 'difficulty']
