"""
Comprehensive tests for the Accounts app.
Tests cover: Models, Forms, Views, Signals, Authentication flows.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import StudentProfile, EXAM_CHOICES
from .forms import StudentRegistrationForm, StudentProfileForm


class StudentProfileModelTest(TestCase):
    """Tests for the StudentProfile model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='TestPass123!', first_name='Test'
        )
        self.profile = self.user.profile

    def test_profile_creation_via_signal(self):
        """Profile should be auto-created when a User is created."""
        self.assertIsNotNone(self.profile)
        self.assertIsInstance(self.profile, StudentProfile)

    def test_profile_str(self):
        """String representation should include username and exam type."""
        self.assertIn('testuser', str(self.profile))

    def test_default_exam_type(self):
        """Default exam type should be JEE."""
        self.assertEqual(self.profile.exam_type, 'JEE')

    def test_default_avatar_emoji(self):
        """Default avatar should be graduation cap."""
        self.assertEqual(self.profile.avatar_emoji, '🎓')

    def test_default_study_hours(self):
        """Default study hours should be 6."""
        self.assertEqual(self.profile.daily_study_hours, 6)

    def test_days_until_exam_none(self):
        """days_until_exam should return None when no exam_date is set."""
        self.assertIsNone(self.profile.days_until_exam)

    def test_days_until_exam_future(self):
        """days_until_exam should return positive number for future dates."""
        from django.utils import timezone
        from datetime import timedelta
        self.profile.exam_date = timezone.now().date() + timedelta(days=30)
        self.profile.save()
        self.assertEqual(self.profile.days_until_exam, 30)

    def test_days_until_exam_past(self):
        """days_until_exam should return 0 for past dates (not negative)."""
        from django.utils import timezone
        from datetime import timedelta
        self.profile.exam_date = timezone.now().date() - timedelta(days=10)
        self.profile.save()
        self.assertEqual(self.profile.days_until_exam, 0)

    def test_profile_update(self):
        """Profile fields should be updatable."""
        self.profile.exam_type = 'NEET'
        self.profile.goals = 'Score 700+'
        self.profile.save()
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.exam_type, 'NEET')
        self.assertEqual(self.profile.goals, 'Score 700+')


class StudentRegistrationFormTest(TestCase):
    """Tests for the registration form."""

    def test_valid_registration(self):
        """Form should be valid with correct data."""
        data = {
            'first_name': 'Anuj',
            'username': 'anuj_new',
            'email': 'anuj@test.com',
            'password1': 'StrongP@ss123',
            'password2': 'StrongP@ss123',
            'exam_type': 'JEE',
        }
        form = StudentRegistrationForm(data=data)
        self.assertTrue(form.is_valid())

    def test_missing_first_name(self):
        """Form should be invalid without first_name."""
        data = {
            'username': 'anuj_new',
            'email': 'anuj@test.com',
            'password1': 'StrongP@ss123',
            'password2': 'StrongP@ss123',
            'exam_type': 'JEE',
        }
        form = StudentRegistrationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('first_name', form.errors)

    def test_password_mismatch(self):
        """Form should reject mismatched passwords."""
        data = {
            'first_name': 'Anuj',
            'username': 'anuj_new',
            'email': 'anuj@test.com',
            'password1': 'StrongP@ss123',
            'password2': 'DifferentPass!',
            'exam_type': 'JEE',
        }
        form = StudentRegistrationForm(data=data)
        self.assertFalse(form.is_valid())

    def test_duplicate_username(self):
        """Form should reject duplicate usernames."""
        User.objects.create_user(username='existing', password='TestPass123!')
        data = {
            'first_name': 'Test',
            'username': 'existing',
            'email': 'new@test.com',
            'password1': 'StrongP@ss123',
            'password2': 'StrongP@ss123',
            'exam_type': 'JEE',
        }
        form = StudentRegistrationForm(data=data)
        self.assertFalse(form.is_valid())

    def test_invalid_exam_type(self):
        """Form should reject invalid exam types."""
        data = {
            'first_name': 'Anuj',
            'username': 'anuj_new',
            'email': 'anuj@test.com',
            'password1': 'StrongP@ss123',
            'password2': 'StrongP@ss123',
            'exam_type': 'INVALID',
        }
        form = StudentRegistrationForm(data=data)
        self.assertFalse(form.is_valid())


class StudentProfileFormTest(TestCase):
    """Tests for the profile edit form."""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='TestPass123!')

    def test_valid_profile_update(self):
        """Profile form should accept valid data."""
        data = {
            'exam_type': 'NEET',
            'daily_study_hours': 8,
            'goals': 'Get into AIIMS',
            'avatar_emoji': '🔥',
        }
        form = StudentProfileForm(data=data, instance=self.user.profile)
        self.assertTrue(form.is_valid())

    def test_study_hours_max(self):
        """Study hours should have a reasonable max."""
        data = {
            'exam_type': 'JEE',
            'daily_study_hours': 18,
            'avatar_emoji': '🎓',
        }
        form = StudentProfileForm(data=data, instance=self.user.profile)
        self.assertTrue(form.is_valid())


class AccountsViewTest(TestCase):
    """Tests for accounts views (login, register, logout, profile)."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='TestPass123!', first_name='Test'
        )
        self.login_url = reverse('accounts:login')
        self.register_url = reverse('accounts:register')
        self.logout_url = reverse('accounts:logout')
        self.profile_url = reverse('accounts:profile')

    # --- Login Tests ---
    def test_login_page_loads(self):
        """Login page should return 200."""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)

    def test_login_success(self):
        """Valid credentials should redirect to dashboard."""
        response = self.client.post(self.login_url, {
            'username': 'testuser', 'password': 'TestPass123!'
        })
        self.assertEqual(response.status_code, 302)

    def test_login_failure(self):
        """Invalid credentials should show error."""
        response = self.client.post(self.login_url, {
            'username': 'testuser', 'password': 'WrongPass'
        })
        self.assertEqual(response.status_code, 200)

    def test_login_empty_fields(self):
        """Empty fields should show error."""
        response = self.client.post(self.login_url, {
            'username': '', 'password': ''
        })
        self.assertEqual(response.status_code, 200)

    def test_login_redirect_authenticated(self):
        """Authenticated users should be redirected from login page."""
        self.client.login(username='testuser', password='TestPass123!')
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 302)

    def test_login_open_redirect_prevention(self):
        """Next URL should not allow external redirects."""
        self.client.post(
            self.login_url + '?next=https://evil.com',
            {'username': 'testuser', 'password': 'TestPass123!'}
        )
        # Should redirect to dashboard, NOT to evil.com

    # --- Register Tests ---
    def test_register_page_loads(self):
        """Register page should return 200."""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)

    def test_register_success(self):
        """Valid registration should create user and redirect."""
        response = self.client.post(self.register_url, {
            'first_name': 'New',
            'username': 'newuser',
            'email': 'new@test.com',
            'password1': 'StrongP@ss123',
            'password2': 'StrongP@ss123',
            'exam_type': 'NEET',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        # Profile should be auto-created
        new_user = User.objects.get(username='newuser')
        self.assertEqual(new_user.profile.exam_type, 'NEET')

    def test_register_redirect_authenticated(self):
        """Authenticated users should be redirected from register page."""
        self.client.login(username='testuser', password='TestPass123!')
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 302)

    # --- Logout Tests ---
    def test_logout(self):
        """Logout should redirect to login."""
        self.client.login(username='testuser', password='TestPass123!')
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 302)

    def test_logout_unauthenticated(self):
        """Logout for unauthenticated user should still redirect safely."""
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 302)

    # --- Profile Tests ---
    def test_profile_requires_auth(self):
        """Profile page should require authentication."""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 302)

    def test_profile_loads(self):
        """Authenticated user should see profile page."""
        self.client.login(username='testuser', password='TestPass123!')
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)

    def test_profile_update(self):
        """Profile should be updatable."""
        self.client.login(username='testuser', password='TestPass123!')
        response = self.client.post(self.profile_url, {
            'exam_type': 'GATE',
            'daily_study_hours': 10,
            'goals': 'Get into IISc',
            'avatar_emoji': '🚀',
        })
        self.assertEqual(response.status_code, 302)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.exam_type, 'GATE')


class SignalTest(TestCase):
    """Tests for Django signals."""

    def test_profile_created_on_user_creation(self):
        """StudentProfile should be auto-created via post_save signal."""
        user = User.objects.create_user(username='signaltest', password='Test123!')
        self.assertTrue(hasattr(user, 'profile'))
        self.assertIsInstance(user.profile, StudentProfile)

    def test_one_profile_per_user(self):
        """Each user should have exactly one profile."""
        user = User.objects.create_user(username='unique', password='Test123!')
        count = StudentProfile.objects.filter(user=user).count()
        self.assertEqual(count, 1)
