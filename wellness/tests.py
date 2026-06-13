"""
Comprehensive tests for the Wellness app.
Tests cover: Models, Views, AJAX endpoints.
"""
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from .models import WellnessAlert, MindfulnessExercise


class WellnessAlertModelTest(TestCase):
    """Tests for WellnessAlert model."""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='TestPass123!')
        self.alert = WellnessAlert.objects.create(
            user=self.user,
            alert_type='burnout',
            severity='warning',
            title='High Burnout Risk',
            message='Your burnout risk has been high this week.',
            recommended_action='Take a break and do a breathing exercise.',
        )

    def test_alert_creation(self):
        """Alert should be created successfully."""
        self.assertEqual(self.alert.alert_type, 'burnout')
        self.assertFalse(self.alert.is_read)

    def test_alert_str(self):
        """String representation should include alert type."""
        self.assertIn('Burnout Risk', str(self.alert))

    def test_alert_icon(self):
        """icon property should return correct emoji."""
        self.assertEqual(self.alert.icon, '🔥')

    def test_alert_icon_default(self):
        """icon should return default for unknown types."""
        self.alert.alert_type = 'unknown'
        self.assertEqual(self.alert.icon, '📋')

    def test_alert_color(self):
        """color property should return correct color."""
        self.assertEqual(self.alert.color, 'orange')

    def test_alert_color_critical(self):
        """color should be red for critical severity."""
        self.alert.severity = 'critical'
        self.assertEqual(self.alert.color, 'red')

    def test_alert_ordering(self):
        """Alerts should be ordered by -created_at."""
        alert2 = WellnessAlert.objects.create(
            user=self.user, alert_type='tip', severity='info',
            title='Tip', message='Drink water'
        )
        alerts = list(WellnessAlert.objects.filter(user=self.user))
        self.assertEqual(alerts[0], alert2)


class MindfulnessExerciseModelTest(TestCase):
    """Tests for MindfulnessExercise model."""

    def setUp(self):
        self.exercise = MindfulnessExercise.objects.create(
            title='4-7-8 Breathing',
            category='breathing',
            description='Calming breathing technique',
            duration_minutes=5,
            steps='["Inhale for 4 counts", "Hold for 7 counts", "Exhale for 8 counts"]',
            emoji='🌬️',
            difficulty='beginner',
        )

    def test_exercise_creation(self):
        """Exercise should be created successfully."""
        self.assertEqual(self.exercise.title, '4-7-8 Breathing')

    def test_exercise_str(self):
        """String representation should include emoji and title."""
        self.assertIn('Breathing', str(self.exercise))

    def test_steps_json_parseable(self):
        """Steps field should be valid JSON."""
        steps = json.loads(self.exercise.steps)
        self.assertEqual(len(steps), 3)


class WellnessViewTest(TestCase):
    """Tests for wellness views."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='TestPass123!')
        self.client.login(username='testuser', password='TestPass123!')

    def test_alerts_page_loads(self):
        """Alerts page should return 200."""
        response = self.client.get(reverse('wellness:alerts'))
        self.assertEqual(response.status_code, 200)

    def test_alerts_context(self):
        """Alerts page should have unread_count in context."""
        response = self.client.get(reverse('wellness:alerts'))
        self.assertIn('unread_count', response.context)

    def test_exercises_page_loads(self):
        """Exercises page should return 200."""
        response = self.client.get(reverse('wellness:exercises'))
        self.assertEqual(response.status_code, 200)

    def test_exercises_category_filter(self):
        """Exercises should be filterable by category."""
        response = self.client.get(reverse('wellness:exercises') + '?category=breathing')
        self.assertEqual(response.status_code, 200)

    def test_resources_page_loads(self):
        """Resources page should return 200."""
        response = self.client.get(reverse('wellness:resources'))
        self.assertEqual(response.status_code, 200)

    def test_resources_has_helplines(self):
        """Resources should contain crisis helplines."""
        response = self.client.get(reverse('wellness:resources'))
        content = response.content.decode()
        self.assertIn('9152987821', content)  # iCall

    def test_resources_has_study_techniques(self):
        """Resources should contain study techniques."""
        response = self.client.get(reverse('wellness:resources'))
        content = response.content.decode()
        self.assertIn('Pomodoro', content)

    def test_mark_alert_read(self):
        """Marking alert as read should update is_read."""
        alert = WellnessAlert.objects.create(
            user=self.user, alert_type='tip', severity='info',
            title='Test', message='Test message'
        )
        response = self.client.post(
            reverse('wellness:mark_alert_read', kwargs={'pk': alert.pk})
        )
        self.assertEqual(response.status_code, 200)
        alert.refresh_from_db()
        self.assertTrue(alert.is_read)

    def test_mark_alert_nonexistent(self):
        """Marking non-existent alert should return 404."""
        response = self.client.post(
            reverse('wellness:mark_alert_read', kwargs={'pk': 99999})
        )
        self.assertEqual(response.status_code, 404)

    def test_mark_alert_get_not_allowed(self):
        """GET on mark_alert_read should return 405."""
        alert = WellnessAlert.objects.create(
            user=self.user, alert_type='tip', severity='info',
            title='Test', message='Test'
        )
        response = self.client.get(
            reverse('wellness:mark_alert_read', kwargs={'pk': alert.pk})
        )
        self.assertEqual(response.status_code, 405)

    def test_pages_require_auth(self):
        """All wellness pages should require authentication."""
        self.client.logout()
        for url in ['wellness:alerts', 'wellness:exercises', 'wellness:resources']:
            response = self.client.get(reverse(url))
            self.assertEqual(response.status_code, 302, f'{url} should require auth')
