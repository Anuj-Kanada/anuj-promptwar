from django.db import models
from django.contrib.auth.models import User


MOOD_CHOICES = [
    (1, '😢 Terrible'),
    (2, '😟 Bad'),
    (3, '😕 Not Great'),
    (4, '😐 Okay'),
    (5, '🙂 Decent'),
    (6, '😊 Good'),
    (7, '😄 Great'),
    (8, '🤩 Amazing'),
    (9, '🌟 Fantastic'),
    (10, '🔥 On Top of the World'),
]

EMOTION_CHOICES = [
    ('anxious', '😰 Anxious'),
    ('stressed', '😫 Stressed'),
    ('overwhelmed', '🤯 Overwhelmed'),
    ('frustrated', '😤 Frustrated'),
    ('sad', '😢 Sad'),
    ('lonely', '😔 Lonely'),
    ('neutral', '😐 Neutral'),
    ('hopeful', '🤞 Hopeful'),
    ('motivated', '💪 Motivated'),
    ('happy', '😊 Happy'),
    ('confident', '😎 Confident'),
    ('grateful', '🙏 Grateful'),
    ('proud', '🏆 Proud'),
    ('calm', '😌 Calm'),
]


class JournalEntry(models.Model):
    """Daily journal entry with mood tracking and AI analysis."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='journal_entries')
    content = models.TextField(help_text="Write about your day, feelings, study experience...")
    mood_score = models.PositiveIntegerField(choices=MOOD_CHOICES, default=5)
    mood_label = models.CharField(max_length=50, blank=True)
    emotions = models.CharField(max_length=200, blank=True, help_text="Comma-separated emotion tags")

    # AI-generated fields
    ai_summary = models.TextField(blank=True)
    ai_insights = models.TextField(blank=True)
    sentiment_score = models.FloatField(null=True, blank=True)
    dominant_emotion = models.CharField(max_length=50, blank=True)
    burnout_risk = models.FloatField(null=True, blank=True)
    encouragement = models.TextField(blank=True)
    coping_suggestions = models.TextField(blank=True)

    is_analyzed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Journal Entries'
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} — {self.created_at.strftime('%b %d, %Y')}"

    @property
    def mood_emoji(self):
        emojis = {1: '😢', 2: '😟', 3: '😕', 4: '😐', 5: '🙂',
                  6: '😊', 7: '😄', 8: '🤩', 9: '🌟', 10: '🔥'}
        return emojis.get(self.mood_score, '😐')

    @property
    def burnout_level(self):
        if self.burnout_risk is None:
            return 'Unknown'
        if self.burnout_risk < 0.3:
            return 'Low'
        elif self.burnout_risk < 0.6:
            return 'Moderate'
        elif self.burnout_risk < 0.8:
            return 'High'
        return 'Critical'

    @property
    def emotion_list(self):
        if self.emotions:
            return [e.strip() for e in self.emotions.split(',')]
        return []


class MoodLog(models.Model):
    """Quick mood check-in (can be logged multiple times a day)."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mood_logs')
    mood_score = models.PositiveIntegerField(choices=MOOD_CHOICES, default=5)
    energy_level = models.PositiveIntegerField(default=5, help_text="1-10 energy scale")
    anxiety_level = models.PositiveIntegerField(default=5, help_text="1-10 anxiety scale")
    motivation_level = models.PositiveIntegerField(default=5, help_text="1-10 motivation scale")
    quick_note = models.CharField(max_length=280, blank=True)
    logged_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-logged_at']
        indexes = [
            models.Index(fields=['user', '-logged_at']),
        ]

    def __str__(self):
        return f"{self.user.username} — Mood: {self.mood_score}/10 @ {self.logged_at.strftime('%H:%M')}"


class StressTrigger(models.Model):
    """AI-identified stress triggers from journal entries."""
    TRIGGER_TYPES = [
        ('academic', 'Academic Pressure'),
        ('social', 'Social Issues'),
        ('family', 'Family Pressure'),
        ('health', 'Health Concerns'),
        ('sleep', 'Sleep Issues'),
        ('comparison', 'Peer Comparison'),
        ('time', 'Time Management'),
        ('self_doubt', 'Self-Doubt'),
        ('perfectionism', 'Perfectionism'),
        ('other', 'Other'),
    ]

    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='stress_triggers')
    trigger_type = models.CharField(max_length=30, choices=TRIGGER_TYPES)
    trigger_detail = models.CharField(max_length=200)
    severity = models.PositiveIntegerField(default=5, help_text="1-10 severity scale")
    identified_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['entry', 'trigger_type']),
        ]

    def __str__(self):
        return f"{self.get_trigger_type_display()}: {self.trigger_detail[:50]}"
