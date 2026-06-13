from django.db import models
from django.contrib.auth.models import User


class WeeklyReport(models.Model):
    """AI-generated weekly wellness report."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weekly_reports')
    week_start = models.DateField()
    week_end = models.DateField()
    avg_mood = models.FloatField(null=True, blank=True)
    avg_anxiety = models.FloatField(null=True, blank=True)
    avg_energy = models.FloatField(null=True, blank=True)
    total_entries = models.PositiveIntegerField(default=0)
    ai_summary = models.TextField(blank=True)
    key_patterns = models.TextField(blank=True, help_text="JSON array")
    recommendations = models.TextField(blank=True, help_text="JSON array")
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-week_end']
        unique_together = ['user', 'week_start']

    def __str__(self):
        return f"{self.user.username} — Week of {self.week_start}"
