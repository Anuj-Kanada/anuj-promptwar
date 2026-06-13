from django.db import models
from django.contrib.auth.models import User


EXAM_CHOICES = [
    ('NEET', 'NEET'),
    ('JEE', 'JEE (Main/Advanced)'),
    ('CUET', 'CUET'),
    ('CAT', 'CAT'),
    ('GATE', 'GATE'),
    ('UPSC', 'UPSC'),
    ('BOARD_10', 'Board Exams (Class 10)'),
    ('BOARD_12', 'Board Exams (Class 12)'),
    ('OTHER', 'Other'),
]


class StudentProfile(models.Model):
    """Extended user profile with exam-specific details."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    exam_type = models.CharField(max_length=20, choices=EXAM_CHOICES, default='JEE')
    exam_date = models.DateField(null=True, blank=True)
    daily_study_hours = models.PositiveIntegerField(default=6)
    goals = models.TextField(blank=True, help_text="What are your goals for this exam?")
    avatar_emoji = models.CharField(max_length=10, default='🎓')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} — {self.get_exam_type_display()}"

    @property
    def days_until_exam(self):
        """Calculate days remaining until exam."""
        if self.exam_date:
            from django.utils import timezone
            delta = self.exam_date - timezone.now().date()
            return max(delta.days, 0)
        return None
