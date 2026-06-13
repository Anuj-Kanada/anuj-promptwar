"""
Comprehensive tests for the Analytics app.
Tests cover: Models, Views, API endpoints, input validation.
"""
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from .models import WeeklyReport
from journal.models import JournalEntry, MoodLog, StressTrigger


class WeeklyReportModelTest(TestCase):
    """Tests for WeeklyReport model."""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='TestPass123!')
        today = timezone.now().date()
        self.report = WeeklyReport.objects.create(
            user=self.user,
            week_start=today - timedelta(days=7),
            week_end=today,
            avg_mood=7.5,
            avg_anxiety=4.2,
            avg_energy=6.8,
            total_entries=5,
            ai_summary='Good week overall.',
            key_patterns='["consistent study", "good sleep"]',
            recommendations='["Keep up the routine", "Try meditation"]',
        )

    def test_report_creation(self):
        """Report should be created successfully."""
        self.assertEqual(self.report.avg_mood, 7.5)
        self.assertEqual(self.report.total_entries, 5)

    def test_report_str(self):
        """String representation should include username."""
        self.assertIn('testuser', str(self.report))

    def test_report_ordering(self):
        """Reports should be ordered by -week_end."""
        today = timezone.now().date()
        r2 = WeeklyReport.objects.create(
            user=self.user,
            week_start=today,
            week_end=today + timedelta(days=7),
        )
        reports = list(WeeklyReport.objects.filter(user=self.user))
        self.assertEqual(reports[0], r2)

    def test_key_patterns_json(self):
        """key_patterns should be valid JSON."""
        patterns = json.loads(self.report.key_patterns)
        self.assertEqual(len(patterns), 2)

    def test_unique_together(self):
        """Same user + week_start should not allow duplicates."""
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            WeeklyReport.objects.create(
                user=self.user,
                week_start=self.report.week_start,
                week_end=self.report.week_end,
            )


class AnalyticsViewTest(TestCase):
    """Tests for analytics views."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='TestPass123!', first_name='Test'
        )
        self.client.login(username='testuser', password='TestPass123!')

    def test_insights_page_loads(self):
        """Insights page should return 200."""
        response = self.client.get(reverse('analytics:insights'))
        self.assertEqual(response.status_code, 200)

    def test_trends_page_loads(self):
        """Trends page should return 200."""
        response = self.client.get(reverse('analytics:trends'))
        self.assertEqual(response.status_code, 200)

    def test_trends_context(self):
        """Trends page should have chart data in context."""
        response = self.client.get(reverse('analytics:trends'))
        self.assertIn('mood_data', response.context)
        self.assertIn('stats', response.context)
        self.assertIn('days', response.context)

    def test_trends_default_days(self):
        """Default days should be 30."""
        response = self.client.get(reverse('analytics:trends'))
        self.assertEqual(response.context['days'], 30)

    def test_trends_custom_days(self):
        """Custom days parameter should work."""
        response = self.client.get(reverse('analytics:trends') + '?days=7')
        self.assertEqual(response.context['days'], 7)

    def test_trends_invalid_days_string(self):
        """Invalid days (string) should fallback to 30."""
        response = self.client.get(reverse('analytics:trends') + '?days=abc')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['days'], 30)

    def test_trends_negative_days(self):
        """Negative days should be clamped to 1."""
        response = self.client.get(reverse('analytics:trends') + '?days=-100')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['days'], 1)

    def test_trends_huge_days(self):
        """Very large days should be clamped to 365."""
        response = self.client.get(reverse('analytics:trends') + '?days=99999')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['days'], 365)

    def test_trend_data_api(self):
        """API should return JSON with chart data."""
        response = self.client.get(reverse('analytics:trend_data'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('dates', data)
        self.assertIn('moods', data)
        self.assertIn('energy', data)
        self.assertIn('anxiety', data)

    def test_trend_data_with_data(self):
        """API should include mood logs in response."""
        MoodLog.objects.create(user=self.user, mood_score=8, energy_level=7, anxiety_level=3)
        response = self.client.get(reverse('analytics:trend_data'))
        data = json.loads(response.content)
        self.assertEqual(len(data['moods']), 1)
        self.assertEqual(data['moods'][0], 8)

    def test_pages_require_auth(self):
        """All analytics pages should require authentication."""
        self.client.logout()
        for url in ['analytics:insights', 'analytics:trends', 'analytics:trend_data']:
            response = self.client.get(reverse(url))
            self.assertEqual(response.status_code, 302, f'{url} should require auth')

    def test_emotion_distribution(self):
        """Trends should compute emotion distribution from entries."""
        JournalEntry.objects.create(
            user=self.user, content='Test', mood_score=6,
            dominant_emotion='hopeful', is_analyzed=True
        )
        response = self.client.get(reverse('analytics:trends'))
        emotion_counts = json.loads(response.context['emotion_counts'])
        self.assertEqual(emotion_counts.get('hopeful'), 1)

    def test_trigger_distribution(self):
        """Trends should compute trigger distribution."""
        entry = JournalEntry.objects.create(
            user=self.user, content='Test', mood_score=4, is_analyzed=True
        )
        StressTrigger.objects.create(
            entry=entry, trigger_type='academic',
            trigger_detail='Overload', severity=7
        )
        response = self.client.get(reverse('analytics:trends'))
        trigger_data = json.loads(response.context['trigger_data'])
        self.assertIn('Academic', trigger_data['labels'])
