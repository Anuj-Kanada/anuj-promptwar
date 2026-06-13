"""
Comprehensive tests for the Journal app.
Tests cover: Models, Forms, Views, AI Service, AJAX endpoints.
"""
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from .models import JournalEntry, MoodLog, StressTrigger, MOOD_CHOICES, EMOTION_CHOICES
from .forms import JournalEntryForm, MoodLogForm
from .ai_service import _get_fallback_analysis


class JournalEntryModelTest(TestCase):
    """Tests for JournalEntry model."""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='TestPass123!')
        self.entry = JournalEntry.objects.create(
            user=self.user,
            content='Today was stressful but I managed to study well.',
            mood_score=6,
            mood_label='Good',
            dominant_emotion='hopeful',
            burnout_risk=0.4,
            sentiment_score=0.65,
        )

    def test_entry_creation(self):
        """Journal entry should be created successfully."""
        self.assertEqual(self.entry.user, self.user)
        self.assertEqual(self.entry.mood_score, 6)

    def test_entry_str(self):
        """String representation should include username."""
        self.assertIn('testuser', str(self.entry))

    def test_mood_emoji(self):
        """mood_emoji property should return correct emoji."""
        self.assertEqual(self.entry.mood_emoji, '😊')

    def test_mood_emoji_default(self):
        """mood_emoji should return default for invalid score."""
        self.entry.mood_score = 99
        self.assertEqual(self.entry.mood_emoji, '😐')

    def test_burnout_level_low(self):
        """burnout_level should be Low for risk < 0.3."""
        self.entry.burnout_risk = 0.1
        self.assertEqual(self.entry.burnout_level, 'Low')

    def test_burnout_level_moderate(self):
        """burnout_level should be Moderate for 0.3-0.6."""
        self.entry.burnout_risk = 0.4
        self.assertEqual(self.entry.burnout_level, 'Moderate')

    def test_burnout_level_high(self):
        """burnout_level should be High for 0.6-0.8."""
        self.entry.burnout_risk = 0.7
        self.assertEqual(self.entry.burnout_level, 'High')

    def test_burnout_level_critical(self):
        """burnout_level should be Critical for risk >= 0.8."""
        self.entry.burnout_risk = 0.9
        self.assertEqual(self.entry.burnout_level, 'Critical')

    def test_burnout_level_none(self):
        """burnout_level should be Unknown when risk is None."""
        self.entry.burnout_risk = None
        self.assertEqual(self.entry.burnout_level, 'Unknown')

    def test_emotion_list(self):
        """emotion_list should parse comma-separated emotions."""
        self.entry.emotions = 'anxious,stressed,hopeful'
        self.assertEqual(self.entry.emotion_list, ['anxious', 'stressed', 'hopeful'])

    def test_emotion_list_empty(self):
        """emotion_list should return empty list for no emotions."""
        self.entry.emotions = ''
        self.assertEqual(self.entry.emotion_list, [])

    def test_ordering(self):
        """Entries should be ordered by -created_at."""
        entry2 = JournalEntry.objects.create(
            user=self.user, content='Second entry', mood_score=7
        )
        entries = list(JournalEntry.objects.filter(user=self.user))
        self.assertEqual(entries[0], entry2)  # Newer first


class MoodLogModelTest(TestCase):
    """Tests for MoodLog model."""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='TestPass123!')

    def test_mood_log_creation(self):
        """MoodLog should be created with valid data."""
        log = MoodLog.objects.create(
            user=self.user, mood_score=8,
            energy_level=7, anxiety_level=3, motivation_level=9
        )
        self.assertEqual(log.mood_score, 8)
        self.assertEqual(log.energy_level, 7)

    def test_mood_log_str(self):
        """String representation should include username and score."""
        log = MoodLog.objects.create(user=self.user, mood_score=5)
        self.assertIn('testuser', str(log))
        self.assertIn('5', str(log))

    def test_mood_log_defaults(self):
        """Default values should be 5."""
        log = MoodLog.objects.create(user=self.user)
        self.assertEqual(log.mood_score, 5)
        self.assertEqual(log.energy_level, 5)


class StressTriggerModelTest(TestCase):
    """Tests for StressTrigger model."""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='TestPass123!')
        self.entry = JournalEntry.objects.create(
            user=self.user, content='Test', mood_score=4
        )

    def test_trigger_creation(self):
        """StressTrigger should be created with valid data."""
        trigger = StressTrigger.objects.create(
            entry=self.entry,
            trigger_type='academic',
            trigger_detail='Too many chapters to cover',
            severity=7,
        )
        self.assertEqual(trigger.trigger_type, 'academic')

    def test_trigger_str(self):
        """String representation should include type display."""
        trigger = StressTrigger.objects.create(
            entry=self.entry,
            trigger_type='self_doubt',
            trigger_detail='Not good enough',
            severity=8,
        )
        self.assertIn('Self-Doubt', str(trigger))

    def test_trigger_cascade_delete(self):
        """Triggers should be deleted when entry is deleted."""
        StressTrigger.objects.create(
            entry=self.entry, trigger_type='sleep',
            trigger_detail='Only 4 hours', severity=6
        )
        self.entry.delete()
        self.assertEqual(StressTrigger.objects.count(), 0)


class JournalEntryFormTest(TestCase):
    """Tests for journal forms."""

    def test_valid_entry_form(self):
        """Form should accept valid content and mood."""
        data = {'content': 'Today was great!', 'mood_score': 8}
        form = JournalEntryForm(data=data)
        self.assertTrue(form.is_valid())

    def test_empty_content(self):
        """Form should reject empty content."""
        data = {'content': '', 'mood_score': 5}
        form = JournalEntryForm(data=data)
        self.assertFalse(form.is_valid())

    def test_clean_emotions_select(self):
        """emotions_select should be joined as comma-separated string."""
        data = {
            'content': 'Test',
            'mood_score': 5,
            'emotions_select': ['anxious', 'stressed'],
        }
        form = JournalEntryForm(data=data)
        if form.is_valid():
            result = form.clean_emotions_select()
            self.assertEqual(result, 'anxious,stressed')


class JournalViewTest(TestCase):
    """Tests for journal views."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='TestPass123!', first_name='Test'
        )
        self.client.login(username='testuser', password='TestPass123!')

    def test_dashboard_loads(self):
        """Dashboard should return 200 for authenticated user."""
        response = self.client.get(reverse('journal:dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_context(self):
        """Dashboard should have required context variables."""
        response = self.client.get(reverse('journal:dashboard'))
        self.assertIn('profile', response.context)
        self.assertIn('mood_data', response.context)
        self.assertIn('streak', response.context)
        self.assertIn('total_entries', response.context)

    def test_dashboard_requires_auth(self):
        """Dashboard should redirect unauthenticated users."""
        self.client.logout()
        response = self.client.get(reverse('journal:dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_new_entry_page_loads(self):
        """New entry page should return 200."""
        response = self.client.get(reverse('journal:new_entry'))
        self.assertEqual(response.status_code, 200)

    def test_history_page_loads(self):
        """History page should return 200."""
        response = self.client.get(reverse('journal:history'))
        self.assertEqual(response.status_code, 200)

    def test_history_date_filter(self):
        """History should filter by days parameter."""
        response = self.client.get(reverse('journal:history') + '?days=7')
        self.assertEqual(response.status_code, 200)

    def test_history_invalid_filter(self):
        """History should handle invalid days gracefully."""
        response = self.client.get(reverse('journal:history') + '?days=abc')
        self.assertEqual(response.status_code, 200)

    def test_entry_detail_404(self):
        """Non-existent entry should return 404."""
        response = self.client.get(reverse('journal:entry_detail', kwargs={'pk': 99999}))
        self.assertEqual(response.status_code, 404)

    def test_entry_detail_other_user(self):
        """User should not see other users' entries."""
        other = User.objects.create_user(username='other', password='Test123!')
        entry = JournalEntry.objects.create(user=other, content='Private', mood_score=5)
        response = self.client.get(reverse('journal:entry_detail', kwargs={'pk': entry.pk}))
        self.assertEqual(response.status_code, 404)

    def test_streak_calculation(self):
        """Streak should count consecutive days with entries."""
        # Create entry for today
        JournalEntry.objects.create(user=self.user, content='Today', mood_score=7)
        response = self.client.get(reverse('journal:dashboard'))
        self.assertGreaterEqual(response.context['streak'], 1)


class QuickMoodLogTest(TestCase):
    """Tests for the AJAX mood log endpoint."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='TestPass123!')
        self.client.login(username='testuser', password='TestPass123!')
        self.url = reverse('journal:quick_mood_log')

    def test_valid_mood_log(self):
        """Valid mood log should return success."""
        response = self.client.post(
            self.url,
            json.dumps({'mood_score': 7, 'quick_note': 'Feeling good'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['mood_score'], 7)

    def test_mood_score_clamp_high(self):
        """Mood score > 10 should be clamped to 10."""
        response = self.client.post(
            self.url,
            json.dumps({'mood_score': 999}),
            content_type='application/json'
        )
        data = json.loads(response.content)
        self.assertEqual(data['mood_score'], 10)

    def test_mood_score_clamp_low(self):
        """Mood score < 1 should be clamped to 1."""
        response = self.client.post(
            self.url,
            json.dumps({'mood_score': 0}),
            content_type='application/json'
        )
        data = json.loads(response.content)
        self.assertEqual(data['mood_score'], 1)

    def test_invalid_json(self):
        """Invalid JSON should return 400."""
        response = self.client.post(self.url, 'not json', content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_get_not_allowed(self):
        """GET request should return 405."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_note_truncation(self):
        """Quick note should be truncated to 280 characters."""
        response = self.client.post(
            self.url,
            json.dumps({'mood_score': 5, 'quick_note': 'x' * 500}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        log = MoodLog.objects.latest('logged_at')
        self.assertLessEqual(len(log.quick_note), 280)


class AIServiceFallbackTest(TestCase):
    """Tests for AI service fallback logic."""

    def test_fallback_analysis_structure(self):
        """Fallback should have all required keys."""
        fallback = _get_fallback_analysis()
        required_keys = [
            'emotional_summary', 'dominant_emotion', 'sentiment_score',
            'hidden_triggers', 'burnout_risk_score',
            'coping_suggestions', 'encouragement_message'
        ]
        for key in required_keys:
            self.assertIn(key, fallback, f'Missing key: {key}')

    def test_fallback_coping_suggestions_count(self):
        """Fallback should have exactly 3 coping suggestions."""
        fallback = _get_fallback_analysis()
        self.assertEqual(len(fallback['coping_suggestions']), 3)

    def test_fallback_sentiment_neutral(self):
        """Fallback sentiment should be neutral (0.5)."""
        fallback = _get_fallback_analysis()
        self.assertEqual(fallback['sentiment_score'], 0.5)

    def test_fallback_no_triggers(self):
        """Fallback should have empty triggers list."""
        fallback = _get_fallback_analysis()
        self.assertEqual(fallback['hidden_triggers'], [])
