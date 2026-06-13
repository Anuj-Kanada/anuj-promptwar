from django.db import models
from django.contrib.auth.models import User


class ChatSession(models.Model):
    """A conversation session with the AI companion."""
    SESSION_TYPES = [
        ('general', 'General Chat'),
        ('stress', 'Stress Relief'),
        ('motivation', 'Motivation Boost'),
        ('breathing', 'Breathing Exercise'),
        ('study_tips', 'Study Tips'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    session_type = models.CharField(max_length=20, choices=SESSION_TYPES, default='general')
    title = models.CharField(max_length=100, default='New Chat')
    is_active = models.BooleanField(default=True)
    started_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username} — {self.title}"

    @property
    def message_count(self):
        return self.messages.count()


class ChatMessage(models.Model):
    """Individual message in a chat session."""
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'MindEase Buddy'),
    ]

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sent_at']
        indexes = [
            models.Index(fields=['session', 'sent_at']),
        ]

    def __str__(self):
        return f"{self.get_role_display()}: {self.content[:50]}..."
