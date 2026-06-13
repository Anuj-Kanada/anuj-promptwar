from django.contrib import admin
from .models import JournalEntry, MoodLog, StressTrigger


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ['user', 'mood_score', 'dominant_emotion', 'burnout_risk', 'is_analyzed', 'created_at']
    list_filter = ['is_analyzed', 'mood_score', 'dominant_emotion']
    search_fields = ['user__username', 'content']


@admin.register(MoodLog)
class MoodLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'mood_score', 'energy_level', 'anxiety_level', 'motivation_level', 'logged_at']
    list_filter = ['mood_score']


@admin.register(StressTrigger)
class StressTriggerAdmin(admin.ModelAdmin):
    list_display = ['entry', 'trigger_type', 'severity', 'identified_at']
    list_filter = ['trigger_type', 'severity']
