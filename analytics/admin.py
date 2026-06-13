from django.contrib import admin
from .models import WeeklyReport

@admin.register(WeeklyReport)
class WeeklyReportAdmin(admin.ModelAdmin):
    list_display = ['user', 'week_start', 'week_end', 'avg_mood', 'total_entries', 'generated_at']
    list_filter = ['week_start']
